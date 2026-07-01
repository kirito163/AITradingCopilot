"""
Riproduzione suoni di notifica
"""

import asyncio
import os
from pathlib import Path
from typing import Optional
from loguru import logger


class SoundPlayer:
    """Gestisce la riproduzione di effetti sonori"""

    def __init__(self, sound_dir: Optional[Path] = None):
        """
        Args:
            sound_dir: Directory contenente i file audio (wav/mp3)
        """
        self.sound_dir = sound_dir or Path(__file__).parent / "sounds"
        self.sound_dir.mkdir(parents=True, exist_ok=True)
        self._enabled = True

        # Suoni predefiniti (cerca file o usa suoni di sistema)
        self.sounds = {
            "alert": self.sound_dir / "alert.wav",
            "trade": self.sound_dir / "trade.wav",
            "info": self.sound_dir / "info.wav",
            "error": self.sound_dir / "error.wav",
        }

    async def play(self, sound_name: str = "alert") -> bool:
        """
        Riproduce un suono

        Args:
            sound_name: Nome del suono (alert, trade, info, error)

        Returns:
            True se riprodotto
        """
        if not self._enabled:
            return False

        try:
            sound_file = self.sounds.get(sound_name)
            if sound_file and sound_file.exists():
                return await self._play_file(str(sound_file))
            else:
                # Fallback: suono di sistema
                return await self._play_system_beep()
        except Exception as e:
            logger.error(f"Errore riproduzione suono '{sound_name}': {e}")
            return False

    async def _play_file(self, filepath: str) -> bool:
        """Riproduce un file audio"""
        try:
            # Prova diverse librerie in ordine
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                return True
            except ImportError:
                pass

            try:
                import playsound
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: playsound.playsound(filepath, False))
                return True
            except ImportError:
                pass

            # Fallback: subprocess con ffplay/afplay
            import subprocess
            import platform
            system = platform.system()
            if system == "Windows":
                cmd = ["start", "/min", "wmplayer", filepath]
            elif system == "Darwin":
                cmd = ["afplay", filepath]
            else:
                cmd = ["paplay", filepath]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            logger.error(f"Impossibile riprodurre {filepath}: {e}")
            return False

    async def _play_system_beep(self) -> bool:
        """Suono di sistema"""
        import platform
        if platform.system() == "Windows":
            import winsound
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: winsound.MessageBeep(winsound.MB_ICONEXCLAMATION))
            return True
        else:
            print("\a")  # Bell character
            return True

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def is_available(self) -> bool:
        return True