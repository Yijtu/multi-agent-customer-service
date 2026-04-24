"""嵌入模型配置。

使用 Chroma 内置的 ONNX MiniLM-L6-v2 嵌入模型，
从 Chroma S3 服务器下载（非 HuggingFace），国内可直接访问。
无需额外安装 sentence-transformers / transformers，避免依赖冲突。
"""

from typing import List

from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from langchain_core.embeddings import Embeddings


class ChromaONNXEmbeddings(Embeddings):
    """基于 Chroma 内置 ONNX 模型的 LangChain Embeddings 适配器。

    封装 chromadb 自带的 all-MiniLM-L6-v2 ONNX 模型，
    使其兼容 LangChain Embeddings 接口。
    """

    def __init__(self) -> None:
        self._ef = ONNXMiniLM_L6_V2()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表。"""
        results = self._ef(texts)
        return [[float(x) for x in vec] for vec in results]

    def embed_query(self, text: str) -> List[float]:
        """嵌入单条查询。"""
        result = self._ef([text])[0]
        return [float(x) for x in result]


def get_embedding_model() -> ChromaONNXEmbeddings:
    """获取嵌入模型实例。

    使用 Chroma 自带的 ONNX MiniLM-L6-v2 模型，
    首次调用时会自动从 Chroma S3 下载（约 80MB）。

    Returns:
        ChromaONNXEmbeddings 实例。
    """
    return ChromaONNXEmbeddings()
