"""
Interfaccia astratta per Speech-to-Text
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from pydantic import BaseModel
from enum import Enum


class STTLanguage(str, Enum):
    IT = "it"
    EN = "en"
    FR = "fr"
    DE = "de"
    ES = "es"
    AUTO = "auto"


class STTResult(BaseModel):
    """Risultato riconoscimento vocale"""
    text: str
    confidence: float = 1.0
    language: Optional[str] = None
    duration_seconds: float = 0.0


class AbstractSTT(ABC):
    """Interfaccia per motore Speech-to-Text"""

    def __init__(self, language: STTLanguage = STTLanguage.IT, **kwargs):
        self.language = language
        self.config = kwargs

    @abstractmethod
    async def transcribe(self, audio_file: str) -> STTResult:
        """
        Trascrive un file audio in testo

        Args:
            audio_file: Percorso del file audio (wav, mp3, ecc.)

        Returns:
            STTResult con testo riconosciuto
        """
        ...

    @abstractmethod
    async def transcribe_stream(self, audio_stream: BinaryIO) -> STTResult:
        """
        Trascrive uno stream audio (per microfoni)

        Args:
            audio_stream: Stream binario

        Returns:
            STTResult
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Verifica se il modello è pronto"""
        ...

    @abstractmethod
    async def get_supported_languages(self) -> list:
        """Elenco lingue supportate"""
        ...