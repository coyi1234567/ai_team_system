#!/usr/bin/env python3
"""
ingest_knowledge_base.py
- 批量导入知识库文件，分块，嵌入，构建Chroma向量库和BM25索引
- 每个知识块元数据包含file/role，便于权限管理
"""
import os
from pathlib import Path
import pickle
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from sklearn.feature_extraction.text import TfidfVectorizer
import glob
import yaml
from chromadb import PersistentClient

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
VECTOR_DB_DIR = BASE_DIR / "../vector_db"
COLLECTION_NAME = "team_knowledge_base"
CHROMA_DIR = (BASE_DIR / "../vector_db/chroma").resolve()

os.makedirs(VECTOR_DB_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# 1. 加载知识库文件（支持txt/markdown/yaml等）
def load_knowledge_files():
    files = glob.glob(str(KNOWLEDGE_DIR / "**/*.*"), recursive=True)
    docs, metadatas = [], []
    for f in files:
        ext = f.split(".")[-1].lower()
        if ext in ["txt", "md"]:
            with open(f, "r", encoding="utf-8") as fin:
                text = fin.read()
            # 简单分块
            blocks = [text[i:i+300] for i in range(0, len(text), 300)]
            for b in blocks:
                docs.append(b)
                metadatas.append({"file": os.path.basename(f), "role": infer_role_from_path(f)})
        elif ext in ["yaml", "yml"]:
            with open(f, "r", encoding="utf-8") as fin:
                ydata = yaml.safe_load(fin)
            # 假设yaml为list，每条为知识块
            for item in ydata:
                docs.append(str(item))
                metadatas.append({"file": os.path.basename(f), "role": infer_role_from_path(f)})
    return docs, metadatas

def infer_role_from_path(f):
    # 简单规则：路径中有role名
    roles = ["boss", "pm", "tech", "frontend", "backend", "algo", "ui", "qa", "devops", "doc"]
    for r in roles:
        if r in f.lower():
            return r
    return "all"

# 2. 嵌入模型
embedder = SentenceTransformer("BAAI/bge-small-zh-v1.5")

# 3. 构建Chroma向量库
def build_chroma(docs, metadatas):
    chroma_client = PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    # 分批导入
    batch = 32
    for i in range(0, len(docs), batch):
        texts = docs[i:i+batch]
        metas = metadatas[i:i+batch]
        embs = embedder.encode(texts).tolist()
        ids = [f"kb_{i+j}" for j in range(len(texts))]
        collection.add(documents=texts, metadatas=metas, embeddings=embs, ids=ids)
    print(f"✅ Chroma向量库已构建，共{len(docs)}条")

# 4. 构建BM25索引
def build_bm25(docs, metadatas):
    vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1,2), max_features=4096)
    tfidf = vectorizer.fit_transform(docs)
    bm25_data = {"vectorizer": vectorizer, "tfidf": tfidf, "texts": docs, "metadatas": metadatas}
    with open(VECTOR_DB_DIR / f"{COLLECTION_NAME}_bm25.pkl", "wb") as f:
        pickle.dump(bm25_data, f)
    print(f"✅ BM25索引已构建，共{len(docs)}条")

if __name__ == "__main__":
    docs, metadatas = load_knowledge_files()
    build_chroma(docs, metadatas)
    build_bm25(docs, metadatas) 