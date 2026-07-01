"""
Modelli Pydantic per il portfolio
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PortfolioSummary(BaseModel):
    """Riepilogo portafoglio"""
    total_value: float = 0.0
    total_cost: float = 0.0
    total_pnl_eur: float = 0.0
    total_pnl_pct: float = 0.0
    daily_pnl_eur: float = 0.0
    daily_pnl_pct: float = 0.0
    open_positions: int = 0
    closed_positions: int = 0
    roi: float = 0.0
    drawdown: float = 0.0
    volatility: float = 0.0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    holdings: List[Dict[str, Any]] = Field(default_factory=list)
    recent_trades: List[Dict[str, Any]] = Field(default_factory=list)
    performance_week: float = 0.0
    performance_month: float = 0.0
    performance_year: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class HoldingCreate(BaseModel):
    """Dati per creazione posizione"""
    asset: str
    symbol: Optional[str] = None
    asset_type: str = "stock"
    quantity: float = Field(gt=0)
    entry_price: float = Field(gt=0)
    broker: str = "paper_trading"
    notes: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class HoldingUpdate(BaseModel):
    """Aggiornamento posizione"""
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None


class ClosePositionRequest(BaseModel):
    """Richiesta chiusura posizione"""
    exit_price: float = Field(gt=0)
    exit_reason: str = "manual"
    notes: Optional[str] = None