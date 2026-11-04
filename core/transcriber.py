import os

import requests
from pydub import AudioSegment

SARVAM_PIECE_SECONDS = 25
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"

_model = None
_model_name = None


def _transcription_backend() -> str:
    """Return the configured STT backend.

    ``RENDER`` is set automatically by Render. On a 512 MB free instance,
    loading Whisper locally is not viable, so default to the Sarvam API.
    """
    backend = os.getenv("TRANSCRIPTION_BACKEND", "").strip().lower()
    if backend:
        return backend
    if os.getenv("RENDER"):
        return "sarvam"
    return "whisper"


def load_model():
    import whisper

    global _model, _model_name
    model_name = os.getenv("WHISPER_MODEL", "small")
    if _model is None or _model_name != model_name:
        print(f"Loading Whisper Model: {model_name}...")
        _model = whisper.load_model(model_name)
        _model_name = model_name
        print("Whisper Model Loaded Successfully")

    return _model


def transcribe_chunk_whisper(chunk_path: str) -> str:
    model = load_model()

    result = model.transcribe(chunk_path)

    return result["text"]


def _send_to_sarvam(piece_path: str, language: str = "english") -> str:
    api_key = os.getenv("SARVAM_API_KEY")
    model_name = os.getenv("SARVAM_STT_MODEL", "saaras:v4").strip()
    headers = {"api-subscription-key": api_key}

    is_hinglish = language.lower() == "hinglish"
    mode = "translate" if is_hinglish else "transcribe"
    language_code = "unknown" if is_hinglish else "en-IN"

    # v2.5 and older models only exist on the legacy translate endpoint.
    # v3/v4 use /speech-to-text with an explicit mode and language code.
    legacy = model_name.startswith("saaras:v2") or model_name.startswith("saarika")
    url = SARVAM_STT_TRANSLATE_URL if legacy else SARVAM_STT_URL
    data = {"model": model_name, "with_diarization": "false"}
    if not legacy:
        data["mode"] = mode
        data["language_code"] = language_code

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )
        if not response.ok:
            print(f"\n Sarvam returned {response.status_code}")
            print(f"Response body:  {response.text}\n")
            response.raise_for_status()

        return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str, language: str = "english") -> str:
    if not os.getenv("SARVAM_API_KEY"):
        raise RuntimeError("SARVAM_API_KEY is not set in environment /.env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_piecs = (len(audio) + piece_ms - 1) // piece_ms
    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start:start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f" -> Sarvam piece {i + 1}/{total_piecs}...")
            full_text += _send_to_sarvam(piece_path, language=language) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    if _transcription_backend() == "sarvam":
        return transcribe_chunk_sarvam(chunk_path, language=language)
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path, language=language)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = ""
    engine = (
        "Sarvam AI"
        if _transcription_backend() == "sarvam" or language.lower() == "hinglish"
        else "Whisper"
    )
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunks {i+1}/{len(chunks)}....")
        text = transcribe_chunk(chunk, language=language)

        full_transcript += text + " "

    print("Transcription Completed!")

    return full_transcript
