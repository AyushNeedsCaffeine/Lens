"""Small text splitter that avoids importing the heavy sentence-transformers
stack pulled in by langchain_text_splitters' package initializer.
"""


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if chunk_size <= 0:
        return [text]
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        chunk_overlap = 0

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            window = text[start:end]
            split_at = max(
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind(" "),
            )
            if split_at > chunk_size // 2:
                end = start + split_at + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break

        next_start = end - chunk_overlap
        start = next_start if next_start > start else end

    return chunks
