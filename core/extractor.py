from core.llm import chat


def _extract(transcript: str, system_prompt: str) -> str:
    return chat(system_prompt, transcript, temperature=0.2)


def extract_action_items(transcript: str) -> str:
    return _extract(
        transcript,
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide: \n"
        "- Task Description \n"
        "- Owner (Who is responsible) \n"
        "- Deadline (if mentioned, else write 'Not specified') \n\n"
        "Format as a numbered list. If none found say 'No action items found.'",
    )


def extract_key_decisions(transcript: str) -> str:
    return _extract(
        transcript,
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decision found.'",
    )


def extract_questions(transcript: str) -> str:
    return _extract(
        transcript,
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'",
    )
