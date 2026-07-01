"""
Provider TTS: Piper (locale, veloce)
"""

import tempfile
import os
import asyncio
from loguru import logger

from voice.tts_base import AbstractTTS


class PiperTTS(AbstractTTS):
    """Sintesi vocale con Piper"""

    def __init__(self, model_path: str, executable: str = "piper", **kwargs):
        super().__init__(**kwargs)
        self.model_path = model_path
        self.executable = executable

    async def speak(self, text: str, voice: str = "default") -> bytes:
        """Genera audio bytes WAV"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name

        try:
            # Piper command: echo "text" | piper --model model.onnx --output_file out.wav
            cmd = f'echo "{text}" | {self.executable} --model {self.model_path} --output_file {out_path}'
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            if os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    audio_data = f.read()
                return audio_data
            else:
                logger.error("Piper non ha prodotto output")
                return b""
        except Exception as e:
            logger.error(f"Errore Piper: {e}")
            return b""
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)

    async def speak_to_file(self, text: str, output_path: str, voice: str = "default") -> bool:
        audio = await self.speak(text, voice)
        if audio:
            with open(output_path, "wb") as f:
                f.write(audio)
            return True
        return False

    async def is_available(self) -> bool:
        """Verifica che piper sia installato e il modello esista"""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.executable, "--help",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()
            return proc.returncode == 0 and os.path.exists(self.model_path)
        except:
            return False

    async def get_available_voices(self) -> list:
        return ["default"]