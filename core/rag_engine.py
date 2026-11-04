from core.llm import chat
from core.vector_store import build_vector_store, load_vector_store

RAG_SYSTEM_PROMPT = """You are an expert meeting assistant. Answer the user's question
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say:
'I could not find this information in the meeting transcript.'

Always be concise and practical. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}"""


class RagChat:
    def __init__(self, vector_store, k: int = 4) -> None:
        self.vector_store = vector_store
        self.k = k

    def invoke(self, question: str) -> str:
        docs = self.vector_store.similarity_search(question, k=self.k)
        context = "\n\n".join(doc.page_content for doc in docs)
        return chat(RAG_SYSTEM_PROMPT.format(context=context), question)


def build_rag_chain(transcript: str, collection_name: str = None) -> RagChat:
    vector_store = build_vector_store(transcript, collection_name=collection_name)
    return RagChat(vector_store)


def load_rag_chain(collection_name: str = None) -> RagChat:
    return RagChat(load_vector_store(collection_name=collection_name))


def ask_question(rag_chain, question: str) -> str:
    print(f"Question: {question}")
    answer = rag_chain.invoke(question)
    print(f"answer: {answer}")
    return answer
