"""
Classi base e interfacce per provider AI
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DecisionType(str, Enum):
    """Tipi di decisioni AI"""
    HOLD = "HOLD"
    BUY = "BUY"
    SELL = "SELL"
    REDUCE_POSITION = "REDUCE_POSITION"
    INCREASE_POSITION = "INCREASE_POSITION"


class RiskLevel(str, Enum):
    """Livelli di rischio"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AIRequest(BaseModel):
    """Richiesta per analisi AI"""
    system_prompt: str
    user_prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, ge=1, le=128000)
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class AIResponse(BaseModel):
    """Risposta strutturata dall'AI"""
    decision: DecisionType
    motivation: str
    probability: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    targets: List[float] = Field(default_factory=list)
    stop_loss: Optional[float] = None
    timeframe: Optional[str] = None  # short_term, medium_term, long_term
    key_indicators: Dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""
    token_usage: Dict[str, int] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_notification_text(self) -> str:
        """Converte in testo per notifica"""
        return (
            f"Decisione: {self.decision.value}\n"
            f"Probabilità: {self.probability:.1f}%\n"
            f"Rischio: {self.risk_level.value}\n"
            f"Motivazione: {self.motivation[:200]}..."
        )
    
    class Config:
        use_enum_values = True


class AbstractAIProvider(ABC):
    """Interfaccia astratta per provider AI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "default",
                 temperature: float = 0.7, max_tokens: int = 1500,
                 timeout: int = 30, **kwargs):
        """
        Inizializza provider AI
        
        Args:
            api_key: API key per il provider
            model: Nome del modello
            temperature: Temperatura per generazione (0-2)
            max_tokens: Token massimi nella risposta
            timeout: Timeout richiesta in secondi
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.config = kwargs
        
    @abstractmethod
    async def analyze_position(self, request: AIRequest) -> AIResponse:
        """
        Analizza una posizione e restituisce decisione strutturata
        
        Args:
            request: AIRequest con prompt e parametri
            
        Returns:
            AIResponse con decisione e analisi
        """
        pass
    
    @abstractmethod
    async def generate_text(self, prompt: str, system: str = "",
                           context: List[Dict[str, str]] = None) -> str:
        """
        Genera testo per conversazioni generiche
        
        Args:
            prompt: Testo del prompt
            system: Prompt di sistema
            context: Contesto conversazione precedente
            
        Returns:
            Testo generato
        """
        pass
    
    @abstractmethod
    async def analyze_market(self, asset: str, indicators: Dict[str, Any]) -> AIResponse:
        """
        Analizza condizioni di mercato per un asset
        
        Args:
            asset: Simbolo dell'asset
            indicators: Indicatori tecnici
            
        Returns:
            AIResponse con analisi
        """
        pass
    
    @abstractmethod
    async def suggest_opportunities(self, portfolio: Dict[str, Any],
                                   market_data: Dict[str, Any],
                                   risk_profile: str = "moderate") -> List[Dict[str, Any]]:
        """
        Suggerisce nuove opportunità di investimento
        
        Args:
            portfolio: Stato attuale portafoglio
            market_data: Dati di mercato disponibili
            risk_profile: Profilo di rischio
            
        Returns:
            Lista di opportunità suggerite
        """
        pass
    
    async def validate_api_key(self) -> bool:
        """
        Verifica validità API key
        
        Returns:
            True se la key è valida
        """
        try:
            await self.generate_text("test", "Respond with 'ok'")
            return True
        except:
            return False
    
    async def get_available_models(self) -> List[str]:
        """
        Ottiene lista modelli disponibili
        
        Returns:
            Lista nomi modelli
        """
        return [self.model]
    
    def _parse_response_to_json(self, raw_response: str) -> Dict[str, Any]:
        """
        Parsa risposta AI in JSON strutturato
        
        Args:
            raw_response: Risposta testuale AI
            
        Returns:
            Dizionario strutturato
        """
        import json
        import re
        
        # Prova a estrarre JSON dalla risposta
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: parsing manuale
        return {"decision": "HOLD", "raw_text": raw_response}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"