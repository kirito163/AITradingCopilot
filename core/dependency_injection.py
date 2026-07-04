"""
Container per Dependency Injection
Gestisce la creazione e l'iniezione delle dipendenze
"""

from typing import Optional, Dict, Any
from pathlib import Path

from loguru import logger

from config.settings import settings
from database.connection import DatabaseManager
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.anthropic_provider import AnthropicProvider
#from ai.providers.gemini_provider import GeminiProvider #TOGLIERE COMMENTO UNA VOTLA IMPLEMENTATO IL MODULO
#from ai.providers.openrouter_provider import OpenRouterProvider #TOGLIERE COMMENTO UNA VOTLA IMPLEMENTATO IL MODULO
from ai.providers.ollama_provider import OllamaProvider
from ai.base import AbstractAIProvider
from portfolio.portfolio_manager import PortfolioManager
from notifications.manager import NotificationManager
from market.providers.yahoo_finance import YahooFinanceProvider
from market.base import AbstractMarketData
from voice.stt_base import AbstractSTT
from voice.tts_base import AbstractTTS
from voice.stt_providers.whisper_local import WhisperLocalSTT
from voice.stt_providers.vosk import VoskSTT
from voice.tts_providers.piper import PiperTTS
from voice.model_manager import VoiceModelManager

# Modello di catalogo -> motore che sa caricarlo
_STT_MODEL_ENGINE = {
    "whisper-base-it": "whisper_local",
    "whisper-small-it": "whisper_local",
    "vosk-model-it-0.22": "vosk",
}
_TTS_MODEL_ENGINE = {
    "piper-it-voice1": "piper",
}

class Container:
    """
    Container per dependency injection
    Gestisce ciclo di vita dei servizi
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
        
        # Inizializza servizi base
        self.settings = settings
        
        logger.info("Container DI creato")
    
    async def init_database(self):
        """Inizializza il database"""
        if "database" not in self._services:
            self._services["database"] = DatabaseManager(settings.database_url)
            await self._services["database"].initialize()
        return self._services["database"]
    
    @property
    def database(self) -> DatabaseManager:
        """Ottieni istanza database"""
        if "database" not in self._services:
            raise RuntimeError("Database non inizializzato")
        return self._services["database"]
    
    @property
    def ai_provider(self) -> AbstractAIProvider:
        """Ottieni provider AI configurato"""
        if "ai_provider" not in self._services:
            self._services["ai_provider"] = self._create_ai_provider()
        return self._services["ai_provider"]
    
    @property
    def market_data(self) -> AbstractMarketData:
        """Ottieni provider market data configurato"""
        if "market_data" not in self._services:
            self._services["market_data"] = self._create_market_data_provider()
        return self._services["market_data"]
    
    @property
    def portfolio_manager(self) -> PortfolioManager:
        """Ottieni portfolio manager"""
        if "portfolio_manager" not in self._services:
            self._services["portfolio_manager"] = PortfolioManager(
                database=self.database,
                market_data=self.market_data
            )
        return self._services["portfolio_manager"]
    
    @property
    def notifications(self) -> NotificationManager:
        """Ottieni notification manager"""
        if "notifications" not in self._services:
            self._services["notifications"] = NotificationManager(
                settings=self.settings,
                tts_provider=self.tts_provider if settings.voice_notifications else None
            )
        return self._services["notifications"]
    
    @property
    def voice_model_manager(self) -> VoiceModelManager:
        """Ottieni il gestore dei modelli vocali locali (STT/TTS)"""
        if "voice_model_manager" not in self._services:
            self._services["voice_model_manager"] = VoiceModelManager(
                models_dir=str(self.settings.models_dir)
            )
        return self._services["voice_model_manager"]
    
    @property
    def stt_provider(self) -> Optional[AbstractSTT]:
        """Ottieni provider Speech-to-Text configurato"""
        if "stt_provider" not in self._services:
            self._services["stt_provider"] = self._create_stt_provider()
        return self._services["stt_provider"]
    
    @property
    def tts_provider(self) -> Optional[AbstractTTS]:
        """Ottieni provider Text-to-Speech configurato"""
        if "tts_provider" not in self._services:
            self._services["tts_provider"] = self._create_tts_provider()
        return self._services["tts_provider"]
    
    def _create_ai_provider(self) -> AbstractAIProvider:
        """Crea provider AI basato sulla configurazione"""
        provider_name = self.settings.ai_provider.lower()
        
        providers = {
            "openai": lambda: OpenAIProvider(
                api_key=self.settings.openai_api_key or self.settings.ai_api_key,
                model=self.settings.ai_model,
                temperature=self.settings.ai_temperature,
                max_tokens=self.settings.ai_max_tokens,
                timeout=self.settings.ai_timeout
            ),
            "anthropic": lambda: AnthropicProvider(
                api_key=self.settings.anthropic_api_key,
                model=self.settings.ai_model,
                temperature=self.settings.ai_temperature,
                max_tokens=self.settings.ai_max_tokens
            ),
            #TOGLIERE COMMENTO UNA VOTLA IMPLEMENTATO IL MODULO
            #"gemini": lambda: GeminiProvider(
            #    api_key=self.settings.gemini_api_key,
            #    model=self.settings.ai_model,
            #    temperature=self.settings.ai_temperature
            #),
            #TOGLIERE COMMENTO UNA VOTLA IMPLEMENTATO IL MODULO
            #"openrouter": lambda: OpenRouterProvider(
            #    api_key=self.settings.openrouter_api_key,
            #    model=self.settings.ai_model,
            #    temperature=self.settings.ai_temperature
            #),
            "ollama": lambda: OllamaProvider(
                base_url=self.settings.ollama_base_url,
                model=self.settings.ai_model,
                temperature=self.settings.ai_temperature
            )
        }
        
        if provider_name in providers:
            logger.info(f"Creazione provider AI: {provider_name}")
            return providers[provider_name]()
        else:
            logger.warning(f"Provider AI '{provider_name}' non trovato, uso OpenAI default")
            return OpenAIProvider(
                api_key=self.settings.ai_api_key,
                model="gpt-3.5-turbo"
            )
    
    def _create_market_data_provider(self) -> AbstractMarketData:
        """Crea provider market data basato sulla configurazione"""
        provider_name = self.settings.market_data_provider.lower()
        
        providers = {
            "yahoo_finance": lambda: YahooFinanceProvider(),
            # Altri provider verranno aggiunti
        }
        
        if provider_name in providers:
            logger.info(f"Creazione provider market data: {provider_name}")
            return providers[provider_name]()
        else:
            logger.warning(f"Provider '{provider_name}' non trovato, uso Yahoo Finance")
            return YahooFinanceProvider()
    
    def _create_stt_provider(self) -> Optional[AbstractSTT]:
        """Crea provider STT se configurato e se il modello è installato"""
        if not self.settings.stt_enabled or self.settings.stt_provider == "disabled":
            return None
 
        model_name = self.settings.stt_model_name
        installed = {m.name: m for m in self.voice_model_manager.get_installed_models()}
        model_info = installed.get(model_name)
        if model_info is None:
            logger.warning(f"Modello STT '{model_name}' non installato: STT disabilitato")
            return None
 
        engine = _STT_MODEL_ENGINE.get(model_name, self.settings.stt_provider)
        model_file_dir = Path(model_info.installed_path)
        # Il file scaricato è l'unico file non-json presente nella cartella del modello
        model_files = [f for f in model_file_dir.iterdir() if f.suffix != ".json"]
        model_path = str(model_files[0]) if model_files else str(model_file_dir)
 
        logger.info(f"Creazione provider STT '{engine}' con modello '{model_name}'")
        if engine == "whisper_local":
            return WhisperLocalSTT(model_path=model_path)
        elif engine == "vosk":
            return VoskSTT(model_path=model_path)
 
        logger.warning(f"Motore STT '{engine}' non supportato")
        return None
 
    def _create_tts_provider(self) -> Optional[AbstractTTS]:
        """Crea provider TTS se configurato e se il modello è installato"""
        if not self.settings.tts_enabled or self.settings.tts_provider == "disabled":
            return None
 
        model_name = self.settings.tts_model_name
        installed = {m.name: m for m in self.voice_model_manager.get_installed_models()}
        model_info = installed.get(model_name)
        if model_info is None:
            logger.warning(f"Modello TTS '{model_name}' non installato: TTS disabilitato")
            return None
 
        engine = _TTS_MODEL_ENGINE.get(model_name, self.settings.tts_provider)
        model_file_dir = Path(model_info.installed_path)
        model_files = [f for f in model_file_dir.iterdir() if f.suffix != ".json"]
        model_path = str(model_files[0]) if model_files else str(model_file_dir)
 
        logger.info(f"Creazione provider TTS '{engine}' con modello '{model_name}'")
        if engine == "piper":
            return PiperTTS(model_path=model_path)
 
        logger.warning(f"Motore TTS '{engine}' non supportato")
        return None
    
    async def close(self):
        """Chiude tutte le connessioni e risorse"""
        logger.info("Chiusura container DI...")
        
        # Chiudi connessioni database
        if "database" in self._services:
            await self._services["database"].close()
        
        # Cancella servizi
        self._services.clear()
        self._initialized = False
        
        logger.info("Container DI chiuso")