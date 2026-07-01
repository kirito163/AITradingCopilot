"""
Classi base per provider broker
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
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


@dataclass
class Order:
    """Ordine di trading"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    commission: float = 0.0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class BrokerPosition:
    """Posizione presso broker"""
    symbol: str
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class AccountInfo:
    """Informazioni account broker"""
    account_id: str
    currency: str = "EUR"
    balance: float = 0.0
    equity: float = 0.0
    margin_used: float = 0.0
    margin_available: float = 0.0
    buying_power: float = 0.0


class AbstractBroker(ABC):
    """Interfaccia astratta per provider broker"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.secret_key = secret_key
        self.config = kwargs
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connette al broker"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnette dal broker"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Ottiene informazioni account"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[BrokerPosition]:
        """Ottiene posizioni aperte"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """
        Piazza un ordine
        
        Args:
            order: Ordine da eseguire
            
        Returns:
            Ordine aggiornato con stato
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancella un ordine"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Ottiene stato ordine"""
        pass
    
    @abstractmethod
    async def get_order_history(self, limit: int = 50) -> List[Order]:
        """Ottiene storico ordini"""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Verifica connessione"""
        return self._connected