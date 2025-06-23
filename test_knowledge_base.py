#!/usr/bin/env python3
"""
测试知识库功能
"""
import chromadb
from chromadb.config import Settings
import pickle
from pathlib import Path
import numpy as np

# 配置路径
BASE_DIR = Path(__file__).parent
VECTOR_DB_DIR = BASE_DIR / "vector_db"

def test_chroma_vector_search():
    """测试Chroma向量搜索"""
    print("🔍 测试Chroma向量搜索...")
    
    try:
        chroma_client = chromadb.Client(Settings(
            persist_directory=str(VECTOR_DB_DIR)
        ))
        
        # 测试每个角色的collection
        roles = ["qa_engineer", "backend_dev", "frontend_dev", "product_manager"]
        
        for role in roles:
            try:
                collection = chroma_client.get_collection(name=f"{role}_kb")
                print(f"  ✅ {role} collection存在，共 {collection.count()} 条记录")
                
                # 测试查询
                results = collection.query(
                    query_texts=["如何测试软件"],
                    n_results=3
                )
                if results and results.get('documents') and results['documents']:
                    print(f"    查询结果: {len(results['documents'][0])} 条")
                else:
                    print(f"    查询结果: 0 条")
                
            except Exception as e:
                print(f"  ❌ {role} collection测试失败: {e}")
                
    except Exception as e:
        print(f"❌ Chroma测试失败: {e}")

def test_bm25_keyword_search():
    """测试BM25关键词搜索"""
    print("\n🔍 测试BM25关键词搜索...")
    
    try:
        roles = ["qa_engineer", "backend_dev", "frontend_dev", "product_manager"]
        
        for role in roles:
            bm25_file = VECTOR_DB_DIR / f"{role}_bm25.pkl"
            
            if bm25_file.exists():
                with open(bm25_file, "rb") as f:
                    bm25_data = pickle.load(f)
                
                print(f"  ✅ {role} BM25索引存在")
                print(f"    文档数量: {len(bm25_data['texts'])}")
                print(f"    特征维度: {bm25_data['tfidf'].shape}")
                
                # 测试关键词搜索
                query = "测试"
                query_vector = bm25_data['vectorizer'].transform([query])
                scores = (bm25_data['tfidf'] * query_vector.T).toarray().flatten()
                
                # 获取top3结果
                top_indices = np.argsort(scores)[-3:][::-1]
                print(f"    关键词'{query}'搜索结果:")
                for i, idx in enumerate(top_indices):
                    if scores[idx] > 0:
                        print(f"      {i+1}. 分数: {scores[idx]:.3f}")
                        print(f"         文本: {bm25_data['texts'][idx][:100]}...")
            else:
                print(f"  ❌ {role} BM25索引文件不存在")
                
    except Exception as e:
        print(f"❌ BM25测试失败: {e}")

def test_hybrid_search():
    """测试混合搜索（向量+关键词）"""
    print("\n🔍 测试混合搜索...")
    
    try:
        chroma_client = chromadb.Client(Settings(
            persist_directory=str(VECTOR_DB_DIR)
        ))
        
        role = "qa_engineer"
        
        # 1. 向量搜索
        collection = chroma_client.get_collection(name=f"{role}_kb")
        vector_results = collection.query(
            query_texts=["软件测试方法"],
            n_results=5
        )
        
        # 2. 关键词搜索
        bm25_file = VECTOR_DB_DIR / f"{role}_bm25.pkl"
        with open(bm25_file, "rb") as f:
            bm25_data = pickle.load(f)
        
        query = "测试"
        query_vector = bm25_data['vectorizer'].transform([query])
        scores = (bm25_data['tfidf'] * query_vector.T).toarray().flatten()
        keyword_indices = np.argsort(scores)[-5:][::-1]
        
        print(f"  📊 {role} 混合搜索结果:")
        print(f"    向量搜索: {len(vector_results.get('documents', [[]])[0])} 条")
        print(f"    关键词搜索: {len(keyword_indices)} 条")
        
        # 合并结果
        all_results = set()
        if vector_results and vector_results.get('documents') and vector_results['documents']:
            for doc in vector_results['documents'][0]:
                all_results.add(doc[:100])  # 取前100字符作为标识
        
        for idx in keyword_indices:
            if scores[idx] > 0:
                all_results.add(bm25_data['texts'][idx][:100])
        
        print(f"    合并后唯一结果: {len(all_results)} 条")
        
    except Exception as e:
        print(f"❌ 混合搜索测试失败: {e}")

if __name__ == "__main__":
    print("🧪 开始测试知识库功能...")
    
    test_chroma_vector_search()
    test_bm25_keyword_search()
    test_hybrid_search()
    
    print("\n✅ 知识库测试完成！") 