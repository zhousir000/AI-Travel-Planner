from pydantic import BaseModel


class SpeechTranscriptionResponse(BaseModel):
    transcript: str
    confidence: float | None = None
    provider: str | None = None

