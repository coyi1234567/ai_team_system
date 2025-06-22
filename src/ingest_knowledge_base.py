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

# 配置路径
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
VECTOR_DB_DIR.mkdir(exist_ok=True)

# 句向量模型
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
embedder = SentenceTransformer(EMBED_MODEL)

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