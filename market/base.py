"""
Classi base per provider market data
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"
    FOREX = "forex"
    INDEX = "index"


@dataclass
class MarketPrice:
    """Prezzo di mercato"""
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: float = 0.0
    change_24h: float = 0.0
    change_pct_24h: float = 0.0
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MarketNews:
    """Notizia di mercato"""
    title: str
    summary: str
    url: str
    source: str
    sentiment: Optional[float] = None  # -1 a 1
    published_at: datetime = None
    related_assets: List[str] = None
    
    def __post_init__(self):
        if self.related_assets is None:
            self.related_assets = []


@dataclass
class TechnicalIndicators:
    """Indicatori tecnici"""
    symbol: str
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    volume_sma: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario"""
        return {
            "rsi": self.rsi,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "sma_20": self.sma_20,
            "sma_50": self.sma_50,
            "bollinger_upper": self.bollinger_upper,
            "bollinger_lower": self.bollinger_lower,
            "atr": self.atr
        }


class AbstractMarketData(ABC):
    """Interfaccia astratta per provider dati di mercato"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self._cache = {}
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[MarketPrice]:
        """
        Ottiene prezzo corrente per un simbolo
        
        Args:
            symbol: Simbolo asset
            
        Returns:
            MarketPrice o None
        """
        pass
    
    @abstractmethod
    async def get_historical_prices(self, symbol: str, 
                                   start_date: datetime,
                                   end_date: datetime = None,
                                   interval: str = "1d") -> List[MarketPrice]:
        """
        Ottiene prezzi storici
        
        Args:
            symbol: Simbolo
            start_date: Data inizio
            end_date: Data fine
            interval: Intervallo (1m, 5m, 15m, 1h, 1d, 1w)
            
        Returns:
            Lista MarketPrice
        """
        pass
    
    @abstractmethod
    async def get_technical_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """
        Ottiene indicatori tecnici
        
        Args:
            symbol: Simbolo asset
            
        Returns:
            TechnicalIndicators
        """
        pass
    
    @abstractmethod
    async def get_news(self, symbol: str, limit: int = 10) -> List[MarketNews]:
        """
        Ottiene news per un asset
        
        Args:
            symbol: Simbolo
            limit: Numero massimo news
            
        Returns:
            Lista MarketNews
        """
        pass
    
    @abstractmethod
    async def get_sentiment(self, symbol: str) -> Optional[float]:
        """
        Ottiene sentiment score per asset
        
        Args:
            symbol: Simbolo
            
        Returns:
            Score da -1 (negativo) a 1 (positivo)
        """
        pass
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, MarketPrice]:
        """
        Ottiene prezzi multipli
        
        Args:
            symbols: Lista simboli
            
        Returns:
            Dizionario symbol -> MarketPrice
        """
        prices = {}
        for symbol in symbols:
            try:
                price = await self.get_current_price(symbol)
                if price:
                    prices[symbol] = price
            except Exception:
                pass
        return prices
    
    async def cache_news_sentiment(self, symbol: str, 
                                  news: List[MarketNews], 
                                  sentiment: Optional[float]):
        """Salva in cache news e sentiment"""
        self._cache[symbol] = {
            "news": news,
            "sentiment": sentiment,
            "timestamp": datetime.now()
        }
    
    async def validate_connection(self) -> bool:
        """Verifica connessione al provider"""
        try:
            await self.get_current_price("AAPL")
            return True
        except:
            return False