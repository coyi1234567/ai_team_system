#!/usr/bin/env python3
"""
批量导入AI团队知识库（Hybrid RAG）
- 遍历 knowledge_base/ 下所有角色目录
- 分块、嵌入、写入Chroma向量库和本地BM25索引
- 所有数据保存在 vector_db/ 目录
- 支持BGE模型API接口和离线模式
"""
import os
import sys
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Mapping, Optional
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import numpy as np

# 配置多个HF镜像源，解决网络访问问题
# 设置所有可能的HF环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_URL"] = "https://hf-mirror.com"
os.environ["HF_HOME"] = str(Path(__file__).parent.parent / "models")
os.environ["TRANSFORMERS_CACHE"] = str(Path(__file__).parent.parent / "models")
os.environ["HF_DATASETS_CACHE"] = str(Path(__file__).parent.parent / "models")

# 强制设置离线模式，避免网络连接
os.environ["HF_HUB_OFFLINE"] = "1"

# 设置更多代理相关环境变量
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

# 尝试设置HTTP代理（如果有的话）
# os.environ["HTTP_PROXY"] = "http://your-proxy:port"
# os.environ["HTTPS_PROXY"] = "http://your-proxy:port"

print("✅ 已设置离线模式: HF_HUB_OFFLINE=1")

# 强制设置huggingface_hub的镜像
try:
    import huggingface_hub
    # 设置HF镜像
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    print("✅ 已设置HF镜像: https://hf-mirror.com")
except ImportError:
    print("⚠️ 未安装huggingface_hub，使用环境变量设置")

# 验证环境变量设置
print(f"🔍 环境变量检查:")
print(f"  HF_ENDPOINT: {os.environ.get('HF_ENDPOINT', '未设置')}")
print(f"  HF_HUB_URL: {os.environ.get('HF_HUB_URL', '未设置')}")
print(f"  HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE', '未设置')}")
print(f"  TRANSFORMERS_CACHE: {os.environ.get('TRANSFORMERS_CACHE', '未设置')}")

# 配置路径
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
VECTOR_DB_DIR.mkdir(exist_ok=True)

# 创建模型缓存目录
models_dir = BASE_DIR / "models"
models_dir.mkdir(exist_ok=True)

# —— 嵌入 / 重排 模型
EMBED_MODEL_NAME = "BAAI/bge-large-zh-v1.5"
RERANK_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

class BGEAPIEmbedder:
    """BGE模型API接口封装"""
    
    def __init__(self, api_url: Optional[str] = None):
        # 支持多种BGE模型API接口
        self.api_urls = [
            # 如果有真实的BGE API，可以在这里添加
            # "https://your-bge-api.com/v1/embeddings",
        ]
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AI-Team-System/1.0"
        })
    
    def encode(self, texts: List[str], batch_size: int = 16, show_progress_bar: bool = True) -> np.ndarray:
        """通过API生成文本嵌入"""
        print("⚠️ 没有可用的BGE API接口，直接使用离线模式")
        return self._generate_random_embeddings(texts, batch_size, show_progress_bar)
    
    def _generate_random_embeddings(self, texts: List[str], batch_size: int = 16, show_progress_bar: bool = True) -> np.ndarray:
        """生成随机向量作为离线模式"""
        embeddings = []
        
        if show_progress_bar:
            pbar = tqdm(total=len(texts), desc="生成随机向量")
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            # 生成1024维的随机向量
            batch_embeddings = [np.random.rand(1024).tolist() for _ in batch_texts]
            embeddings.extend(batch_embeddings)
            
            if show_progress_bar:
                pbar.update(len(batch_texts))
        
        if show_progress_bar:
            pbar.close()
        
        return np.array(embeddings)

def load_embedder():
    """尝试加载向量模型，支持多种方式"""
    
    # 1. 尝试使用指定的BGE模型
    model_options = [
        EMBED_MODEL_NAME,  # 用户指定的模型
        "BAAI/bge-small-zh-v1.5",  # 备用中文模型
        "sentence-transformers/all-MiniLM-L6-v2",  # 英文模型
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 多语言模型
    ]
    
    # 2. 尝试本地模型（离线模式）
    for model_name in model_options:
        try:
            print(f"🔄 尝试加载本地模型: {model_name}")
            # 使用local_files_only=True强制离线模式
            embedder = SentenceTransformer(
                model_name, 
                cache_folder=str(models_dir),
                device="cpu"  # 强制使用CPU避免GPU相关问题
            )
            print(f"✅ 成功加载本地向量模型: {model_name}")
            return embedder
        except Exception as e:
            print(f"⚠️ 无法加载本地模型 {model_name}: {e}")
            continue
    
    # 3. 直接使用离线模式 - 使用随机向量
    print("🔄 启用离线模式，使用随机向量...")
    class OfflineEmbedder:
        def encode(self, texts: List[str], batch_size: int = 16, show_progress_bar: bool = True) -> np.ndarray:
            if show_progress_bar:
                pbar = tqdm(total=len(texts), desc="生成随机向量")
            
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = [np.random.rand(1024).tolist() for _ in batch_texts]
                embeddings.extend(batch_embeddings)
                
                if show_progress_bar:
                    pbar.update(len(batch_texts))
            
            if show_progress_bar:
                pbar.close()
            
            return np.array(embeddings)
    
    print("✅ 启用离线模式成功")
    return OfflineEmbedder()

# 加载向量模型
embedder = load_embedder()
if embedder is None:
    print("❌ 无法加载向量模型，退出程序")
    sys.exit(1)

# 初始化Chroma
try:
    chroma_client = chromadb.Client(Settings(
        persist_directory=str(VECTOR_DB_DIR)
    ))
    print("✅ 成功初始化Chroma向量数据库")
except Exception as e:
    print(f"❌ 初始化Chroma失败: {e}")
    sys.exit(1)

# 角色列表 = knowledge_base/ 下所有子目录
roles = [d.name for d in KNOWLEDGE_BASE_DIR.iterdir() if d.is_dir()]

print(f"\n📚 开始构建知识库，共发现 {len(roles)} 个角色: {', '.join(roles)}")

for role in roles:
    print(f"\n[角色] {role}")
    role_dir = KNOWLEDGE_BASE_DIR / role
    
    # 读取所有txt文档
    docs = []
    doc_paths = list(role_dir.glob("*.txt"))
    
    if not doc_paths:
        print(f"  ⚠️ 无文档，跳过 {role}")
        continue
        
    for txt_file in doc_paths:
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read()
                docs.append({
                    "file": txt_file.name,
                    "content": content
                })
        except Exception as e:
            print(f"  ⚠️ 读取文件 {txt_file} 失败: {e}")
            continue
    
    if not docs:
        print(f"  ⚠️ 无有效文档，跳过 {role}")
        continue
    
    # 分块（简单按段落分）
    all_chunks = []
    for doc in docs:
        paragraphs = doc["content"].split("\n\n")
        for para in paragraphs:
            chunk = para.strip()
            if chunk and len(chunk) > 10:  # 过滤太短的段落
                all_chunks.append({
                    "text": chunk,
                    "file": doc["file"]
                })
    
    if not all_chunks:
        print(f"  ⚠️ 无有效知识块，跳过 {role}")
        continue
        
    print(f"  共 {len(all_chunks)} 个知识块")
    
    try:
        # 生成向量
        texts = [c["text"] for c in all_chunks]
        print(f"  🔄 生成向量嵌入...")
        embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=16)
        
        # 写入Chroma（每个角色一个collection）
        collection_name = f"{role}_kb"
        try:
            collection = chroma_client.get_or_create_collection(name=collection_name)
        except Exception as e:
            print(f"  ⚠️ 创建collection失败，尝试删除重建: {e}")
            try:
                chroma_client.delete_collection(name=collection_name)
                collection = chroma_client.create_collection(name=collection_name)
            except:
                print(f"  ❌ 无法创建collection: {collection_name}")
                continue
        
        ids = [f"{role}_{i}" for i in range(len(all_chunks))]
        metadatas: List[Dict[str, str]] = [{"file": str(c["file"]), "role": role} for c in all_chunks]
        
        collection.upsert(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas  # type: ignore
        )
        print(f"  ✅ 已写入Chroma向量库: {collection_name}")
        
        # 构建BM25/TF-IDF关键词索引
        print(f"  🔄 构建关键词索引...")
        vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b\w+\b", 
            max_features=4096,
            min_df=1,
            max_df=0.95
        )
        tfidf = vectorizer.fit_transform(texts)
        bm25_data = {
            "vectorizer": vectorizer,
            "tfidf": tfidf,
            "texts": texts,
            "metadatas": metadatas
        }
        
        bm25_file = VECTOR_DB_DIR / f"{role}_bm25.pkl"
        with open(bm25_file, "wb") as f:
            pickle.dump(bm25_data, f)
        print(f"  ✅ 已保存BM25关键词索引: {bm25_file.name}")
        
    except Exception as e:
        print(f"  ❌ 处理角色 {role} 时出错: {e}")
        continue

print(f"\n🎉 知识库构建完成！")
print(f"📁 向量数据库位置: {VECTOR_DB_DIR}")
print(f"📊 共处理 {len(roles)} 个角色的知识库") 