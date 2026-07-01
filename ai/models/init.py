"""
Modelli Pydantic per AI
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class PositionAnalysis(BaseModel):
    """Modello per analisi posizione"""
    asset: str
    decision: str
    probability: float
    risk_level: str
    motivation: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    targets: List[float] = Field(default_factory=list)
    stop_loss: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class MarketSentiment(BaseModel):
    """Modello sentiment mercato"""
    asset: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)
    summary: str
    timestamp: datetime = Field(default_factory=datetime.now)


class TradeSuggestion(BaseModel):
    """Modello suggerimento trade"""
    asset: str
    action: str  # BUY, SELL
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    position_size_pct: float = Field(ge=0.0, le=100.0)
    rationale: str
    risk_reward_ratio: float
    timestamp: datetime = Field(default_factory=datetime.now)