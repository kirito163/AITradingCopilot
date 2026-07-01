"""
Voice Module - Speech-to-Text e Text-to-Speech
"""

from .stt_base import AbstractSTT, STTResult
from .tts_base import AbstractTTS, TTSRequest
from .model_manager import VoiceModelManager

__all__ = ['AbstractSTT', 'STTResult', 'AbstractTTS', 'TTSRequest', 'VoiceModelManager']