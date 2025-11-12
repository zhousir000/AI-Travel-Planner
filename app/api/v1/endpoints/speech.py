from fastapi import APIRouter, Depends, File, Form, UploadFile

from ....schemas.speech import SpeechTranscriptionResponse
from ....services.speech_service import SpeechService

router = APIRouter()


@router.post("/transcribe", response_model=SpeechTranscriptionResponse)
async def transcribe_speech(
    audio: UploadFile | None = File(default=None, description="Audio file in PCM/WAV format"),
    transcript_text: str | None = Form(default=None),
    language: str = Form(default="zh_cn"),
):
    service = SpeechService()
    return await service.transcribe(audio_file=audio, transcript_text=transcript_text, language=language)
