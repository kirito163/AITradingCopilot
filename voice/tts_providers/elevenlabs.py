"""
Provider TTS: ElevenLabs (cloud, alta qualità)
"""

import httpx
from typing import Optional
from loguru import logger

from voice.tts_base import AbstractTTS


class ElevenLabsTTS(AbstractTTS):
    """Sintesi vocale ElevenLabs"""

    def __init__(self, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.voice_id = voice_id
        self.client = httpx.AsyncClient(
            base_url="https://api.elevenlabs.io/v1",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            timeout=30
        )

    async def speak(self, text: str, voice: str = "default") -> bytes:
        """Genera audio MP3"""
        try:
            response = await self.client.post(
                f"/text-to-speech/{self.voice_id}",
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
            )
            response.raise_for_status()
            return response.content  # MP3 bytes
        except Exception as e:
            logger.error(f"Errore ElevenLabs: {e}")
            return b""

    async def speak_to_file(self, text: str, output_path: str, voice: str = "default") -> bool:
        audio = await self.speak(text, voice)
        if audio:
            with open(output_path, "wb") as f:
                f.write(audio)
            return True
        return False

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def get_available_voices(self) -> list:
        try:
            resp = await self.client.get("/voices")
            voices = resp.json().get("voices", [])
            return [v["name"] for v in voices]
        except:
            return []

    async def close(self):
        await self.client.aclose()