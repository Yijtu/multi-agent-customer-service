"""知识库索引构建脚本。

读取 data/knowledge/ 目录下的文档，分块后写入 Chroma 向量数据库。
支持增量判断：如果 Chroma 数据库已存在且文档未变化，跳过重建。
"""

import os

from config import CHROMA_DB_PATH, KNOWLEDGE_DIR


def build_index(force: bool = False) -> None:
    """构建或加载知识库索引。

    Args:
        force: 是否强制重建索引（即使已存在）。
    """
    from rag.document_loader import load_knowledge_docs
    from rag.vector_store import init_vector_store

    # 检查知识库目录是否存在
    if not os.path.exists(KNOWLEDGE_DIR):
        print("   ⚠️ 知识库目录不存在，跳过 RAG 索引构建")
        return

    # 检查是否需要重建
    if os.path.exists(CHROMA_DB_PATH) and not force:
        print("📚 RAG 知识库已存在，加载中...")
        init_vector_store()
        return

    # 构建新索引
    print("📚 构建 RAG 知识库索引...")
    docs = load_knowledge_docs()
    if not docs:
        print("   ⚠️ 没有找到文档，跳过索引构建")
        return

    init_vector_store(documents=docs)
    print("📚 RAG 知识库索引构建完成！")


if __name__ == "__main__":
    # 可直接运行此脚本强制重建索引
    build_index(force=True)
