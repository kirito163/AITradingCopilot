"""
Modelli Pydantic per il modulo Voice
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VoiceModelInfo(BaseModel):
    """Informazioni su un modello vocale"""
    name: str
    provider: str  # stt o tts
    language: str = "it"
    version: str = "1.0"
    size_mb: float = 0.0
    installed: bool = False
    installed_path: Optional[str] = None
    last_updated: Optional[datetime] = None
    download_url: Optional[str] = None


class VoiceSettings(BaseModel):
    """Configurazione voce"""
    stt_provider: str = "disabled"
    tts_provider: str = "disabled"
    stt_language: str = "it"
    tts_voice: str = "default"
    tts_speed: float = 1.0
    auto_download_models: bool = True
    use_gpu: bool = False