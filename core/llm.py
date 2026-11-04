"""Lightweight Mistral client.

The LangChain Mistral integration imports ``langchain_core.language_models``,
which eagerly tries to import ``transformers`` (and therefore PyTorch). On a
512 MB Render instance that overhead is enough to push the process over the
limit, so the app talks to the Mistral API through the official SDK instead.
"""

import os
from functools import lru_cache

from mistralai import Mistral


@lru_cache(maxsize=1)
def get_client() -> Mistral:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not set in environment /.env")
    return Mistral(api_key=api_key)


def get_model() -> str:
    return os.getenv("MISTRAL_MODEL", "ministral-8b-latest")


def _content_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(getattr(item, "text", "")))
        return "".join(parts).strip()
    return str(content).strip()


def chat(system_prompt: str, user_text: str, temperature: float = 0.3) -> str:
    response = get_client().chat.complete(
        model=get_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=temperature,
    )
    return _content_to_text(response.choices[0].message.content)


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    if not texts:
        return []

    model = os.getenv("MISTRAL_EMBEDDING_MODEL", "mistral-embed")
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        response = get_client().embeddings.create(
            model=model,
            inputs=texts[start:start + batch_size],
        )
        vectors.extend(list(item.embedding) for item in response.data)
    return vectors
