"""
Pydantic Settings globali
Configurazioni dell'applicazione
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from pathlib import Path


class Settings(BaseSettings):
    """Configurazioni globali AI Trading Copilot"""
    
    # Application
    app_name: str = "AI Trading Copilot"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///trading_copilot.db"
    
    # AI Provider Configuration
    ai_provider: str = Field(default="openai", description="Provider AI predefinito")
    ai_model: str = Field(default="gpt-4o", description="Modello AI predefinito")
    ai_api_key: Optional[str] = Field(default=None, description="API Key AI")
    ai_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    ai_max_tokens: int = Field(default=1500, ge=1, le=128000)
    ai_timeout: int = Field(default=30, ge=1, le=300)
    
    # Multiple AI Provider Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # Broker Configuration
    broker_provider: str = Field(default="paper_trading", description="Broker predefinito")
    ib_gateway_host: str = "127.0.0.1"
    ib_gateway_port: int = 7497
    ib_client_id: int = 1
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    coinbase_api_key: Optional[str] = None
    coinbase_secret_key: Optional[str] = None
    kraken_api_key: Optional[str] = None
    kraken_secret_key: Optional[str] = None
    
    # Market Data Configuration
    market_data_provider: str = Field(default="yahoo_finance")
    alpha_vantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None
    twelve_data_api_key: Optional[str] = None
    
    # Voice Configuration
    stt_enabled: bool = Field(default=False, description="Abilita riconoscimento vocale")
    tts_enabled: bool = Field(default=False, description="Abilita sintesi vocale")
    stt_provider: str = Field(default="disabled", description="Speech-to-Text provider")
    tts_provider: str = Field(default="disabled", description="Text-to-Speech provider")
    stt_model_name: str = Field(default="whisper-base-it", description="Modello STT selezionato dal catalogo")
    tts_model_name: str = Field(default="piper-it-voice1", description="Modello TTS selezionato dal catalogo")
    whisper_model_size: str = "base"  # tiny, base, small, medium, large
    elevenlabs_api_key: Optional[str] = None
    voice_language: str = "it-IT"
    
    # Monitoring
    monitoring_enabled: bool = False
    monitoring_interval_minutes: int = Field(default=5, ge=1, le=1440)
    auto_update_prices: bool = True
    
    # Notifications
    popup_enabled: bool = True
    sound_enabled: bool = False
    voice_notifications: bool = False
    sound_volume: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # UI Configuration
    theme: str = Field(default="light", pattern="^(light|dark)$")
    language: str = "it"
    window_width: int = 1400
    window_height: int = 900
    enable_animations: bool = True
    
    # AI Prompts Configuration
    default_prompt_profile: str = "swing_trader"
    custom_system_prompt: Optional[str] = None
    
    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_file: str = "logs/trading_copilot.log"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"
    
    # Proxy
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    # Data directories
    data_dir: Path = Path("./data")
    models_dir: Path = Path("./models")
    
    class Config:
        env_prefix = "AI_TRADING_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Istanza globale delle settings
settings = Settings()