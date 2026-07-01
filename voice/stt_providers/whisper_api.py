"""
Provider STT: OpenAI Whisper API
"""

import httpx
from pathlib import Path
from typing import Optional
from loguru import logger

from voice.stt_base import AbstractSTT, STTResult, STTLanguage


class WhisperAPI(AbstractSTT):
    """Utilizza OpenAI Whisper API per trascrizione"""

    def __init__(self, api_key: str, language: STTLanguage = STTLanguage.IT, **kwargs):
        super().__init__(language=language, **kwargs)
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )

    async def transcribe(self, audio_file: str) -> STTResult:
        """Invia file audio a OpenAI"""
        try:
            with open(audio_file, "rb") as f:
                files = {"file": (Path(audio_file).name, f, "audio/wav")}
                data = {
                    "model": "whisper-1",
                    "language": self.language.value if self.language != STTLanguage.AUTO else None,
                    "response_format": "json"
                }
                response = await self.client.post("/audio/transcriptions", files=files, data=data)
                response.raise_for_status()
                result = response.json()
                return STTResult(
                    text=result.get("text", ""),
                    confidence=0.95,
                    language=result.get("language", self.language.value)
                )
        except Exception as e:
            logger.error(f"Errore Whisper API: {e}")
            return STTResult(text="", confidence=0.0)

    async def transcribe_stream(self, audio_stream) -> STTResult:
        raise NotImplementedError("API non supporta streaming diretto")

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def get_supported_languages(self) -> list:
        return ["it", "en", "fr", "de", "es", "auto"]

    async def close(self):
        await self.client.aclose()