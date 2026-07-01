# voice/tts_providers/coqui.py
"""
Provider TTS: Coqui TTS - Stub
"""

from voice.tts_base import AbstractTTS

class CoquiTTS(AbstractTTS):
    async def speak(self, text: str, voice: str = "default") -> bytes:
        return b""
    async def speak_to_file(self, text: str, output_path: str, voice: str = "default") -> bool:
        return False
    async def is_available(self) -> bool:
        return False
    async def get_available_voices(self) -> list:
        return []