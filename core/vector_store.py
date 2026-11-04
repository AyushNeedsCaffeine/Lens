from langchain_chroma import Chroma
from langchain_core.documents import Document

from core.embeddings import get_embeddings
from core.text_splitter import split_text

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"


def build_vector_store(transcript: str, collection_name: str = None) -> Chroma:
    print("Building vector store")

    chunks = split_text(transcript, chunk_size=500, chunk_overlap=50)

    docs = [
        Document(page_content=chunk, metadata={"chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name or COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )

    return vector_store


def load_vector_store(collection_name: str = None) -> Chroma:
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=collection_name or COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    return vector_store


def get_retriver(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
