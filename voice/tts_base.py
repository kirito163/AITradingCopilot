"""
Interfaccia astratta per Text-to-Speech
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from pydantic import BaseModel


class TTSRequest(BaseModel):
    """Richiesta sintesi vocale"""
    text: str
    voice: str = "default"
    speed: float = 1.0
    language: str = "it"
    output_format: str = "wav"  # wav, mp3


class AbstractTTS(ABC):
    """Interfaccia per motore Text-to-Speech"""

    def __init__(self, **kwargs):
        self.config = kwargs

    @abstractmethod
    async def speak(self, text: str, voice: str = "default") -> bytes:
        """
        Converte testo in audio bytes

        Args:
            text: Testo da sintetizzare
            voice: Voce da usare

        Returns:
            Audio bytes (WAV)
        """
        ...

    @abstractmethod
    async def speak_to_file(self, text: str, output_path: str, voice: str = "default") -> bool:
        """Salva audio su file"""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Verifica disponibilità del motore"""
        ...

    @abstractmethod
    async def get_available_voices(self) -> list:
        """Elenco voci disponibili"""
        ...