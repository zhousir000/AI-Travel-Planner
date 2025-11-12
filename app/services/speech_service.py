import base64
import hashlib
import json
import time
from typing import Any

import httpx
from fastapi import HTTPException, UploadFile, status

from ..core.config import settings
from ..schemas.speech import SpeechTranscriptionResponse


class SpeechService:
    def __init__(self) -> None:
        self.provider = settings.speech_provider.lower()

    async def transcribe(
        self,
        *,
        audio_file: UploadFile | None = None,
        transcript_text: str | None = None,
        language: str = "zh_cn",
    ) -> SpeechTranscriptionResponse:
        if self.provider == "web":
            if transcript_text:
                return SpeechTranscriptionResponse(transcript=transcript_text, provider="web", confidence=1.0)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcript text is required.")
        if self.provider == "iflytek":
            if not audio_file:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is required.")
            return await self._iflytek_transcribe(audio_file, language=language)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported speech provider")

    async def _iflytek_transcribe(self, audio_file: UploadFile, language: str) -> SpeechTranscriptionResponse:
        if not (settings.iflytek_app_id and settings.iflytek_api_key):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="iFlyTek credentials missing")
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file")
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        params = {
            "engine_type": "sms16k",
            "aue": "raw",
            "language": language,
        }
        x_param = base64.b64encode(json.dumps(params).encode("utf-8")).decode("utf-8")
        cur_time = str(int(time.time()))
        checksum = hashlib.md5((settings.iflytek_api_key + cur_time + x_param).encode("utf-8")).hexdigest()
        headers = {
            "X-Appid": settings.iflytek_app_id,
            "X-CurTime": cur_time,
            "X-Param": x_param,
            "X-CheckSum": checksum,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.xfyun.cn/v1/service/v1/iat",
                headers=headers,
                data={"audio": audio_b64},
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"iFlyTek error: {response.status_code} {response.text}",
            )
        payload: dict[str, Any] = response.json()
        if payload.get("code") != "0" and payload.get("code") != 0:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"iFlyTek error: {payload.get('desc') or payload}",
            )
        transcript = payload.get("data")
        if not transcript:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="iFlyTek response missing data")
        return SpeechTranscriptionResponse(transcript=transcript, provider="iflytek", confidence=None)
