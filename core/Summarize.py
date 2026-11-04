from core.llm import chat
from core.text_splitter import split_text


def split_transcript(transcript: str) -> list:
    return split_text(transcript, chunk_size=3000, chunk_overlap=200)


def summarize(transcript: str) -> str:
    chunks = split_transcript(transcript)
    chunk_summaries = [
        chat(
            "Summarize this portion of a meeting transcript concisely.",
            chunk,
        )
        for chunk in chunks
    ]
    combined = "\n\n".join(chunk_summaries)

    return chat(
        "You are an expert meeting summarizer. Combine these partial summaries "
        "into one final professional meeting summary in bullet points.",
        combined,
    )


def generate_title(transcript: str) -> str:
    return chat(
        "Based on the meeting transcript, generate a short professional meeting "
        "title (max 8 words). Only return the title, nothing else.",
        transcript[:2000],
    )
