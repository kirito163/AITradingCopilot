
"""
Gestione download, aggiornamento, cancellazione modelli vocali locali
"""

import os
import shutil
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import httpx

from loguru import logger
from voice.schemas import VoiceModelInfo


class VoiceModelManager:
    """Gestisce i modelli voice (STT/TTS) locali"""

    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._models: Dict[str, VoiceModelInfo] = {}
        self._load_installed_models()

        # Catalogo modelli disponibili
        self._catalog = {
            "whisper-base-it": VoiceModelInfo(
                name="whisper-base-it",
                provider="stt",
                language="it",
                version="1.0",
                size_mb=142.0,
                download_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
            ),
            "whisper-small-it": VoiceModelInfo(
                name="whisper-small-it",
                provider="stt",
                language="it",
                version="1.0",
                size_mb=466.0,
                download_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
            ),
            "piper-it-voice1": VoiceModelInfo(
                name="piper-it-voice1",
                provider="tts",
                language="it",
                version="1.0",
                size_mb=35.0,
                download_url="https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/paola/medium/it_IT-paola-medium.onnx"
            ),
            "vosk-model-it-0.22": VoiceModelInfo(
                name="vosk-model-it-0.22",
                provider="stt",
                language="it",
                version="0.22",
                size_mb=1300.0,
                download_url="https://alphacephei.com/vosk/models/vosk-model-it-0.22.zip"
            ),
        }

    def _load_installed_models(self):
        """Scansiona la directory modelli e popola lo stato"""
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                meta_file = model_dir / "model_info.json"
                if meta_file.exists():
                    import json
                    with open(meta_file) as f:
                        info = json.load(f)
                    self._models[model_dir.name] = VoiceModelInfo(**info)
                else:
                    # Fallback: deduci dal nome
                    self._models[model_dir.name] = VoiceModelInfo(
                        name=model_dir.name,
                        provider="unknown",
                        installed=True,
                        installed_path=str(model_dir)
                    )

    def get_installed_models(self) -> List[VoiceModelInfo]:
        """Restituisce modelli installati"""
        return list(self._models.values())

    def get_available_models(self) -> List[VoiceModelInfo]:
        """Restituisce tutti i modelli nel catalogo (con flag installed)"""
        available = []
        for name, info in self._catalog.items():
            installed_info = self._models.get(name)
            if installed_info:
                info.installed = True
                info.installed_path = installed_info.installed_path
            else:
                info.installed = False
            available.append(info)
        return available

    async def download_model(self, model_name: str) -> bool:
        """
        Scarica un modello dal catalogo

        Args:
            model_name: Nome modello

        Returns:
            True se scaricato con successo
        """
        if model_name not in self._catalog:
            logger.error(f"Modello {model_name} non trovato nel catalogo")
            return False

        model_info = self._catalog[model_name]
        if not model_info.download_url:
            logger.error(f"Nessun URL di download per {model_name}")
            return False

        target_dir = self.models_dir / model_name
        target_dir.mkdir(parents=True, exist_ok=True)

        file_name = model_info.download_url.split("/")[-1]
        target_file = target_dir / file_name

        try:
            logger.info(f"Scaricamento {model_name} ({model_info.size_mb} MB)...")
            async with httpx.AsyncClient(timeout=3600) as client:
                async with client.stream("GET", model_info.download_url) as response:
                    response.raise_for_status()
                    with open(target_file, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)

            # Salva metadati
            import json
            model_info.installed = True
            model_info.installed_path = str(target_dir)
            model_info.last_updated = datetime.now()
            with open(target_dir / "model_info.json", "w") as f:
                json.dump(model_info.dict(), f, indent=2)

            self._models[model_name] = model_info
            logger.info(f"Modello {model_name} scaricato con successo in {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Errore download modello {model_name}: {e}")
            # Pulisci download parziale
            if target_file.exists():
                target_file.unlink()
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Elimina un modello installato"""
        model_dir = self.models_dir / model_name
        if not model_dir.exists():
            logger.warning(f"Modello {model_name} non trovato")
            return False

        try:
            shutil.rmtree(model_dir)
            if model_name in self._models:
                del self._models[model_name]
            logger.info(f"Modello {model_name} eliminato")
            return True
        except Exception as e:
            logger.error(f"Errore eliminazione modello {model_name}: {e}")
            return False

    def get_disk_usage(self) -> Dict[str, float]:
        """Calcola spazio occupato dai modelli"""
        total_size = 0
        model_sizes = {}
        for name, info in self._models.items():
            model_dir = self.models_dir / name
            if model_dir.exists():
                size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                model_sizes[name] = size / (1024 * 1024)  # MB
                total_size += size
        return {
            "total_mb": total_size / (1024 * 1024),
            "models": model_sizes
        }