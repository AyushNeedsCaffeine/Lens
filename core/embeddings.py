"""Embedding backends that avoid PyTorch in the web process."""

import os

from core.llm import embed_texts


class MistralEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts)

    def embed_query(self, text: str) -> list[float]:
        return embed_texts([text])[0]


class LocalEmbeddings:
    """Chroma's built-in ONNX MiniLM model.

    This is the same model the app used through HuggingFaceEmbeddings, but it
    runs on onnxruntime instead of pulling in torch and sentence-transformers.
    """

    def __init__(self) -> None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._embed = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, vector)) for vector in self._embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(map(float, self._embed([text])[0]))


def get_embeddings():
    backend = os.getenv("EMBEDDING_BACKEND", "").strip().lower()
    if not backend and os.getenv("RENDER") and os.getenv("MISTRAL_API_KEY"):
        backend = "mistral"
    if backend == "mistral":
        return MistralEmbeddings()
    return LocalEmbeddings()
