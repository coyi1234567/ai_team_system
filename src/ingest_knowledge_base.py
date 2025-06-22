#!/usr/bin/env python3
"""
批量导入AI团队知识库（Hybrid RAG）
- 遍历 knowledge_base/ 下所有角色目录
- 分块、嵌入、写入Chroma向量库和本地BM25索引
- 所有数据保存在 vector_db/ 目录
"""
import os
from pathlib import Path
from typing import List, Dict, Mapping
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

# 配置HF镜像，解决网络访问问题
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_URL"] = "https://hf-mirror.com"

# 配置路径
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
VECTOR_DB_DIR.mkdir(exist_ok=True)

# 句向量模型 - 使用中文模型，通过HF镜像下载
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"  # 中文模型，通过镜像下载
try:
    embedder = SentenceTransformer(EMBED_MODEL)
    print(f"✅ 成功加载向量模型: {EMBED_MODEL}")
except Exception as e:
    print(f"⚠️ 无法加载向量模型 {EMBED_MODEL}: {e}")
    print("尝试使用备用模型...")
    try:
        # 备用模型
        EMBED_MODEL = "all-MiniLM-L6-v2"
        embedder = SentenceTransformer(EMBED_MODEL)
        print(f"✅ 成功加载备用向量模型: {EMBED_MODEL}")
    except Exception as e2:
        print(f"❌ 备用模型也无法加载: {e2}")
        print("请检查网络连接或手动下载模型")
        exit(1)

# 初始化Chroma
chroma_client = chromadb.Client(Settings(
    persist_directory=str(VECTOR_DB_DIR)
))

# 角色列表 = knowledge_base/ 下所有子目录
roles = [d.name for d in KNOWLEDGE_BASE_DIR.iterdir() if d.is_dir()]

for role in roles:
    print(f"\n[角色] {role}")
    role_dir = KNOWLEDGE_BASE_DIR / role
    # 读取所有txt文档
    docs = []
    doc_paths = list(role_dir.glob("*.txt"))
    for txt_file in doc_paths:
        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.read()
            docs.append({
                "file": txt_file.name,
                "content": content
            })
    if not docs:
        print(f"  ⚠️ 无文档，跳过 {role}")
        continue
    # 分块（简单按段落分）
    all_chunks = []
    for doc in docs:
        for para in doc["content"].split("\n\n"):
            chunk = para.strip()
            if chunk:
                all_chunks.append({
                    "text": chunk,
                    "file": doc["file"]
                })
    print(f"  共 {len(all_chunks)} 个知识块")
    # 生成向量
    texts = [c["text"] for c in all_chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=32)
    # 写入Chroma（每个角色一个collection）
    collection = chroma_client.get_or_create_collection(
        name=f"{role}_kb"
    )
    ids = [f"{role}_{i}" for i in range(len(all_chunks))]
    metadatas = [{"file": str(c["file"])} for c in all_chunks]
    collection.upsert(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas
    )
    print(f"  ✅ 已写入Chroma向量库: {role}_kb")
    # 构建BM25/TF-IDF关键词索引
    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\\b\\w+\\b", max_features=4096)
    tfidf = vectorizer.fit_transform(texts)
    bm25_data = {
        "vectorizer": vectorizer,
        "tfidf": tfidf,
        "texts": texts,
        "metadatas": metadatas
    }
    with open(VECTOR_DB_DIR / f"{role}_bm25.pkl", "wb") as f:
        pickle.dump(bm25_data, f)
    print(f"  ✅ 已保存BM25关键词索引: {role}_bm25.pkl")

print("\n🎉 所有角色知识库已批量导入并构建索引！") 