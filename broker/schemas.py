"""
Modelli Pydantic per broker e ordini
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderSchema(BaseModel):
    """Schema per ordine di trading"""
    order_id: Optional[str] = None
    symbol: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    quantity: float = Field(gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    commission: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @validator('price')
    def price_required_for_limit(cls, v, values):
        if values.get('order_type') == OrderType.LIMIT and v is None:
            raise ValueError('Price is required for LIMIT orders')
        return v


class PositionSchema(BaseModel):
    """Schema posizione broker"""
    symbol: str
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class AccountInfoSchema(BaseModel):
    """Schema informazioni account"""
    account_id: str
    currency: str = "EUR"
    balance: float = 0.0
    equity: float = 0.0
    margin_used: float = 0.0
    margin_available: float = 0.0
    buying_power: float = 0.0


class BrokerConfig(BaseModel):
    """Configurazione broker"""
    provider: str
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    passphrase: Optional[str] = None
    environment: str = "paper"  # live/paper
    additional_settings: dict = Field(default_factory=dict)