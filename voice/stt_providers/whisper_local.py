"""
Provider STT: Whisper locale (tramite whisper.cpp o openai-whisper)
"""

import os
import subprocess
import tempfile
from typing import Optional
from loguru import logger

from voice.stt_base import AbstractSTT, STTResult, STTLanguage


class WhisperLocalSTT(AbstractSTT):
    """Trascrizione tramite Whisper in locale"""

    def __init__(self, model_path: Optional[str] = None, 
                 language: STTLanguage = STTLanguage.IT, **kwargs):
        super().__init__(language=language, **kwargs)
        # Percorso eseguibile whisper.cpp o modello
        self.model_path = model_path or os.path.expanduser("~/whisper.cpp/models/ggml-base.bin")
        self.executable = kwargs.get("executable", "whisper-cpp")  # o "whisper"

    async def transcribe(self, audio_file: str) -> STTResult:
        """Trascrive file audio usando whisper.cpp"""
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file non trovato: {audio_file}")

        # Converti in wav 16kHz mono se necessario (puoi usare ffmpeg)
        processed_file = audio_file
        if not audio_file.endswith(".wav"):
            processed_file = await self._convert_to_wav(audio_file)

        try:
            cmd = [
                self.executable,
                "-m", self.model_path,
                "-f", processed_file,
                "-l", self.language.value,
                "--output-txt", "--output-json"
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Whisper error: {stderr.decode()}")

            # Leggi output JSON (whisper.cpp salva in file .json con stesso nome)
            json_path = processed_file + ".json"
            if os.path.exists(json_path):
                import json
                with open(json_path) as f:
                    data = json.load(f)
                text = data.get("text", "")
                return STTResult(text=text.strip(), confidence=0.9, language=self.language.value)
            else:
                # Se non trovato, leggi stdout
                text = stdout.decode().strip()
                return STTResult(text=text, confidence=0.8, language=self.language.value)

        except Exception as e:
            logger.error(f"Errore trascrizione whisper locale: {e}")
            return STTResult(text="", confidence=0.0, language=self.language.value)

    async def transcribe_stream(self, audio_stream) -> STTResult:
        """Trascrizione stream non supportata in questa implementazione"""
        raise NotImplementedError("Whisper locale non supporta lo streaming diretto. Salvare prima su file.")

    async def is_available(self) -> bool:
        """Verifica che modello e eseguibile esistano"""
        return os.path.exists(self.model_path) and (
            os.path.exists(self.executable) or 
            subprocess.run(["which", self.executable], capture_output=True).returncode == 0
        )

    async def get_supported_languages(self) -> list:
        return ["it", "en", "fr", "de", "es", "auto"]

    async def _convert_to_wav(self, input_file: str) -> str:
        """Converte audio in wav 16kHz mono con ffmpeg"""
        output_file = tempfile.mktemp(suffix=".wav")
        cmd = [
            "ffmpeg", "-i", input_file,
            "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
            output_file, "-y"
        ]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await process.communicate()
        return output_file