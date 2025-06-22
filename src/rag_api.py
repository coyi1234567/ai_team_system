#!/usr/bin/env python3
"""
rag_api.py
- rag_search(user_id, role, query, top_k=5): 先做权限校验，再做Hybrid检索
- 权限不足直接拒绝
"""
import os
from pathlib import Path
import pickle
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import sys
sys.path.append(str(Path(__file__).parent))
from permission_manager import PermissionManager
from chromadb import PersistentClient

BASE_DIR = Path(__file__).parent.parent
VECTOR_DB_DIR = (BASE_DIR / "../vector_db").resolve()
COLLECTION_NAME = "team_knowledge_base"
CHROMA_DIR = (BASE_DIR / "vector_db/chroma").resolve()

# 初始化
chroma_client = PersistentClient(path=str(CHROMA_DIR))
embedder = SentenceTransformer("BAAI/bge-small-zh-v1.5")
perm_mgr = PermissionManager()

# 检索API
def rag_search(user_id: str, role: str, query: str, top_k: int = 5) -> str:
    """
    1. 权限校验（只返回有权限的知识块）
    2. 向量检索+BM25关键词检索，合并去重，按得分排序
    """
    # 1. 加载Chroma Collection
    try:
        collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    except Exception as e:
        return f"❌ 未找到知识库索引，请先运行 ingest_knowledge_base.py 构建索引\n异常信息: {e}"
    # 2. 加载BM25索引
    bm25_path = VECTOR_DB_DIR / f"{COLLECTION_NAME}_bm25.pkl"
    if not bm25_path.exists():
        return f"❌ 未找到BM25索引，请先运行 ingest_knowledge_base.py 构建索引\n实际路径: {bm25_path}"
    try:
        with open(bm25_path, "rb") as f:
            bm25_data = pickle.load(f)
    except Exception as e:
        return f"❌ 读取BM25索引失败: {e}\n实际路径: {bm25_path}"
    # 3. 先做BM25关键词检索
    vectorizer: TfidfVectorizer = bm25_data["vectorizer"]
    tfidf = bm25_data["tfidf"]
    texts = bm25_data["texts"]
    metadatas = bm25_data["metadatas"]
    query_vec = vectorizer.transform([query])
    bm25_scores = (tfidf @ query_vec.T).toarray().squeeze()
    bm25_top_idx = [int(idx) for idx in list(range(len(bm25_scores))) if bm25_scores[idx] > 0]
    bm25_top_idx = sorted(bm25_top_idx, key=lambda i: bm25_scores[i], reverse=True)[:top_k]
    bm25_results = [(i, float(bm25_scores[i])) for i in bm25_top_idx]
    # 4. 向量检索
    query_emb = embedder.encode([query])
    chroma_where = {"role": role} if role != 'all' else None
    if chroma_where:
        chroma_results = collection.query(
            query_embeddings=query_emb.tolist(),
            n_results=top_k*2,
            where=chroma_where
        )
    else:
        chroma_results = collection.query(
            query_embeddings=query_emb.tolist(),
            n_results=top_k*2
        )
    # 5. 合并去重
    result_dict = {}
    debug_info = []
    # BM25结果
    for i, score in bm25_results:
        meta = metadatas[i] if i < len(metadatas) else {}
        text = texts[i] if i < len(texts) else ""
        doc_id = f"bm25_{i}"
        resource_id = str(meta.get("file", ""))
        debug_info.append(f"BM25: doc_id={doc_id}, resource_id={resource_id}, meta={meta}, has_perm={perm_mgr.has_permission(user_id, role, 'doc', resource_id, 'read')}")
        if not perm_mgr.has_permission(user_id, role, "doc", resource_id, "read"):
            continue
        result_dict[doc_id] = {"text": text, "score": float(score), "source": resource_id}
    # 向量结果
    chroma_docs = chroma_results.get("documents", [[]])
    chroma_metas = chroma_results.get("metadatas", [[]])
    chroma_dists = chroma_results.get("distances", [[]])
    for i, text in enumerate(chroma_docs[0] if chroma_docs else []):
        meta = chroma_metas[0][i] if chroma_metas and len(chroma_metas[0]) > i else {}
        resource_id = str(meta.get("file", ""))
        debug_info.append(f"VEC: doc_id=vec_{resource_id}_{i}, resource_id={resource_id}, meta={meta}, has_perm={perm_mgr.has_permission(user_id, role, 'doc', resource_id, 'read')}")
        if not perm_mgr.has_permission(user_id, role, "doc", resource_id, "read"):
            continue
        doc_id = f"vec_{resource_id}_{i}"
        score = chroma_dists[0][i] if chroma_dists and len(chroma_dists[0]) > i else 0.0
        sim_score = 1.0 - float(score)
        if doc_id not in result_dict or sim_score > result_dict[doc_id]["score"]:
            result_dict[doc_id] = {"text": text, "score": sim_score, "source": resource_id}
    # 6. 按分数排序，返回top_k
    if not result_dict:
        debug_info.append(f"bm25_results_len={len(bm25_results)}, chroma_docs_len={len(chroma_docs[0]) if chroma_docs and len(chroma_docs)>0 else 0}")
        return "\n".join(debug_info) + "\n❌ 当前用户无权限访问任何知识块，或无相关内容"
    sorted_results = sorted(result_dict.values(), key=lambda x: x["score"], reverse=True)[:top_k]
    # 7. 格式化输出
    output = []
    for i, r in enumerate(sorted_results, 1):
        output.append(f"[{i}] 来源: {r['source']}\n分数: {r['score']:.4f}\n内容: {r['text']}\n")
    # 调试：输出所有知识块的role和file
    print(f"[DEBUG] docs={len(texts)}, metadatas={metadatas[:3]} ...")
    return "\n".join(output)

# 示例本地测试
if __name__ == "__main__":
    # 测试用例：user_id/role均为'all'，应有权限
    print(rag_search("all", "all", "项目管理最佳实践")) 