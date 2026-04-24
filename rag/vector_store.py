"""Chroma 向量数据库管理。

负责向量数据库的初始化、文档写入和检索。
使用本地持久化存储，重启后无需重新构建索引。
"""

import os
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from config import CHROMA_DB_PATH

# 延迟导入，避免未安装 chromadb 时直接报错
_vector_store = None


def init_vector_store(documents: Optional[List[Document]] = None):
    """初始化或加载 Chroma 向量数据库。

    如果 CHROMA_DB_PATH 已存在持久化数据，直接加载；
    如果传入 documents，则（重新）构建索引。

    Args:
        documents: 待索引的文档列表。为 None 时仅加载已有数据库。
    """
    global _vector_store

    from langchain_chroma import Chroma
    from rag.embeddings import get_embedding_model

    embedding = get_embedding_model()

    if documents:
        # 有新文档时重建索引
        _vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embedding,
            persist_directory=CHROMA_DB_PATH,
            collection_name="knowledge_base",
        )
        print(f"   ✅ 已索引 {len(documents)} 个文档片段到 Chroma")
    elif os.path.exists(CHROMA_DB_PATH):
        # 加载已有持久化数据
        _vector_store = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embedding,
            collection_name="knowledge_base",
        )
        print("   ✅ 已加载 Chroma 向量数据库")
    else:
        print("   ⚠️ Chroma 数据库不存在，请先运行 build_index()")


def get_retriever(top_k: int = 3, filter_dict: Optional[dict] = None) -> Optional[VectorStoreRetriever]:
    """获取向量检索器。

    Args:
        top_k: 返回的最相关文档数。
        filter_dict: 元数据过滤条件，如 {"category": "tech"}。

    Returns:
        VectorStoreRetriever 实例，未初始化时返回 None。
    """
    global _vector_store

    if _vector_store is None:
        if os.path.exists(CHROMA_DB_PATH):
            init_vector_store()
        else:
            return None

    search_kwargs = {"k": top_k}
    if filter_dict:
        search_kwargs["filter"] = filter_dict

    return _vector_store.as_retriever(search_kwargs=search_kwargs)


def similarity_search(
    query: str,
    top_k: int = 3,
    filter_dict: Optional[dict] = None,
) -> List[Document]:
    """直接执行相似度搜索。

    Args:
        query: 查询文本。
        top_k: 返回的最相关文档数。
        filter_dict: 元数据过滤条件。

    Returns:
        匹配的文档列表。
    """
    global _vector_store

    # 自动初始化：如果尚未加载，尝试加载已有数据库
    if _vector_store is None:
        if os.path.exists(CHROMA_DB_PATH):
            init_vector_store()
        else:
            return []

    if _vector_store is None:
        return []

    kwargs = {}
    if filter_dict:
        kwargs["filter"] = filter_dict

    return _vector_store.similarity_search(query, k=top_k, **kwargs)
