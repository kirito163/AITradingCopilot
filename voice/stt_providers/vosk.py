"""
Provider STT: Vosk (offline, leggero)
"""

import os
import json
import wave
from typing import Optional
from loguru import logger

from voice.stt_base import AbstractSTT, STTResult, STTLanguage


class VoskSTT(AbstractSTT):
    """Trascrizione locale con Vosk"""

    def __init__(self, model_path: str, language: STTLanguage = STTLanguage.IT, **kwargs):
        super().__init__(language=language, **kwargs)
        self.model_path = model_path
        self._model = None
        self._recognizer = None

    async def _load_model(self):
        if self._model is None:
            try:
                from vosk import Model, KaldiRecognizer
                self._model = Model(self.model_path)
                self._recognizer = KaldiRecognizer(self._model, 16000)
                logger.info("Modello Vosk caricato")
            except ImportError:
                raise ImportError("vosk non installato. Esegui: pip install vosk")

    async def transcribe(self, audio_file: str) -> STTResult:
        await self._load_model()
        if not audio_file.endswith(".wav"):
            raise ValueError("Vosk richiede file WAV mono 16kHz")

        wf = wave.open(audio_file, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio deve essere mono 16-bit 16kHz")

        rec = self._recognizer
        rec.SetWords(True)

        full_text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                full_text += res.get("text", "") + " "

        # Ultimi pezzi
        final = json.loads(rec.FinalResult())
        full_text += final.get("text", "")

        return STTResult(
            text=full_text.strip(),
            confidence=0.9,
            language=self.language.value
        )

    async def transcribe_stream(self, audio_stream) -> STTResult:
        await self._load_model()
        rec = self._recognizer
        rec.SetWords(True)
        full_text = ""
        while True:
            data = audio_stream.read(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                full_text += res.get("text", "") + " "
        final = json.loads(rec.FinalResult())
        full_text += final.get("text", "")
        return STTResult(text=full_text.strip(), confidence=0.9)

    async def is_available(self) -> bool:
        return os.path.exists(self.model_path)

    async def get_supported_languages(self) -> list:
        return ["it", "en", "de", "fr", "es"]