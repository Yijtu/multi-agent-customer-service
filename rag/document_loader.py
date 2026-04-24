"""文档加载与分块。

从 data/knowledge/ 目录读取 Markdown 文档，
进行分块处理后返回 Document 列表，用于向量化索引。
"""

import os
from typing import List

from langchain_core.documents import Document

from config import KNOWLEDGE_DIR


def _split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """简单的文本分块器，按段落和标题分割。"""
    # 先按标题分大块
    sections = []
    current = ""
    for line in text.split("\n"):
        if line.startswith("## ") and current.strip():
            sections.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        sections.append(current.strip())

    # 再对超长的 section 做细分
    chunks = []
    for section in sections:
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # 按段落分割
            paragraphs = section.split("\n\n")
            buf = ""
            for para in paragraphs:
                if len(buf) + len(para) > chunk_size and buf:
                    chunks.append(buf.strip())
                    # overlap: 保留尾部
                    buf = buf[-overlap:] + "\n\n" + para
                else:
                    buf += ("\n\n" if buf else "") + para
            if buf.strip():
                chunks.append(buf.strip())

    return chunks


def load_knowledge_docs() -> List[Document]:
    """加载 data/knowledge/ 目录下的所有 Markdown 文档并分块。

    每个文档会被标记 metadata.category（从文件名推断）和 metadata.source。

    Returns:
        分块后的 Document 列表。
    """
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"   ⚠️ 知识库目录不存在: {KNOWLEDGE_DIR}")
        return []

    documents: List[Document] = []

    # 文件名到 category 的映射
    category_map = {
        "products": "product",
        "tech_faq": "tech",
        "policies": "policy",
    }

    for filename in os.listdir(KNOWLEDGE_DIR):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 推断 category
        name_without_ext = os.path.splitext(filename)[0]
        category = category_map.get(name_without_ext, "general")

        # 按标题分段，再做细粒度分块
        chunks_text = _split_text(content, chunk_size=500, overlap=100)

        chunks = [
            Document(
                page_content=chunk,
                metadata={"source": filename, "category": category},
            )
            for chunk in chunks_text
        ]

        documents.extend(chunks)
        print(f"   📄 {filename} → {len(chunks)} 个片段 (category={category})")

    print(f"   📚 共加载 {len(documents)} 个文档片段")
    return documents
