"""
Provider Yahoo Finance
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import numpy as np

from loguru import logger

from market.base import (
    AbstractMarketData, MarketPrice, MarketNews,
    TechnicalIndicators
)


class YahooFinanceProvider(AbstractMarketData):
    """Provider dati di mercato Yahoo Finance"""
    
    def __init__(self, **kwargs):
        super().__init__(api_key=None, **kwargs)
        logger.info("YahooFinance Provider inizializzato")
    
    async def get_current_price(self, symbol: str) -> Optional[MarketPrice]:
        """Ottiene prezzo corrente"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Ottieni prezzo più recente
            hist = ticker.history(period="2d")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            change_24h = current_price - prev_close
            change_pct = (change_24h / prev_close * 100) if prev_close > 0 else 0
            
            return MarketPrice(
                symbol=symbol,
                price=current_price,
                bid=info.get('bid'),
                ask=info.get('ask'),
                volume=hist['Volume'].iloc[-1] if 'Volume' in hist else 0,
                change_24h=change_24h,
                change_pct_24h=change_pct,
                high_24h=hist['High'].iloc[-1] if len(hist) > 0 else None,
                low_24h=hist['Low'].iloc[-1] if len(hist) > 0 else None,
                market_cap=info.get('marketCap')
            )
            
        except Exception as e:
            logger.error(f"Errore prezzo {symbol}: {e}")
            return None
    
    async def get_historical_prices(self, symbol: str,
                                   start_date: datetime,
                                   end_date: datetime = None,
                                   interval: str = "1d") -> List[MarketPrice]:
        """Ottiene prezzi storici"""
        try:
            if end_date is None:
                end_date = datetime.now()
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date, interval=interval)
            
            prices = []
            for idx, row in hist.iterrows():
                prices.append(MarketPrice(
                    symbol=symbol,
                    price=row['Close'],
                    volume=row.get('Volume', 0),
                    high_24h=row.get('High'),
                    low_24h=row.get('Low'),
                    timestamp=idx.to_pydatetime()
                ))
            
            return prices
            
        except Exception as e:
            logger.error(f"Errore prezzi storici {symbol}: {e}")
            return []
    
    async def get_technical_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """Calcola indicatori tecnici"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo")
            
            if hist.empty or len(hist) < 50:
                return None
            
            close_prices = hist['Close']
            high_prices = hist['High']
            low_prices = hist['Low']
            volume = hist['Volume']
            
            # RSI (14 periodi)
            rsi = self._calculate_rsi(close_prices, 14)
            
            # MACD
            macd, macd_signal, macd_hist = self._calculate_macd(close_prices)
            
            # Medie mobili
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            sma_200 = close_prices.rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close_prices)
            
            # ATR
            atr = self._calculate_atr(high_prices, low_prices, close_prices)
            
            return TechnicalIndicators(
                symbol=symbol,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_hist,
                sma_20=sma_20,
                sma_50=sma_50,
                sma_200=sma_200,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                atr=atr,
                volume_sma=volume.rolling(window=20).mean().iloc[-1]
            )
            
        except Exception as e:
            logger.error(f"Errore indicatori tecnici {symbol}: {e}")
            return None
    
    async def get_news(self, symbol: str, limit: int = 10) -> List[MarketNews]:
        """Ottiene news"""
        try:
            ticker = yf.Ticker(symbol)
            news_data = ticker.news[:limit]
            
            news_list = []
            for item in news_data:
                content = item.get('content', {})
                news_list.append(MarketNews(
                    title=content.get('title', ''),
                    summary=content.get('summary', ''),
                    url=content.get('canonicalUrl', {}).get('url', ''),
                    source=content.get('provider', {}).get('displayName', ''),
                    published_at=datetime.fromtimestamp(
                        content.get('pubDate', datetime.now().timestamp())
                    )
                ))
            
            return news_list
            
        except Exception as e:
            logger.error(f"Errore news {symbol}: {e}")
            return []
    
    async def get_sentiment(self, symbol: str) -> Optional[float]:
        """Calcola sentiment approssimativo"""
        try:
            # Yahoo Finance non ha un vero sentiment, usiamo metriche alternative
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Combinazione di vari fattori per un sentiment approssimativo
            recommendation = info.get('recommendationMean', 3)  # 1=Strong Buy, 5=Strong Sell
            target_mean = info.get('targetMeanPrice', 0)
            current_price = info.get('currentPrice', 0)
            
            if current_price == 0:
                return 0.0
            
            # Normalizza recommendation (1-5) in sentiment (-1 a 1)
            rec_sentiment = (3 - recommendation) / 2  # Mappa 1->1, 3->0, 5->-1
            
            # Differenza target price
            if target_mean > 0:
                target_diff = (target_mean - current_price) / current_price
                target_sentiment = max(-1, min(1, target_diff))
            else:
                target_sentiment = 0
            
            # Media pesata
            sentiment = (rec_sentiment * 0.6 + target_sentiment * 0.4)
            
            return round(sentiment, 3)
            
        except Exception as e:
            logger.error(f"Errore sentiment {symbol}: {e}")
            return None
    
    # Metodi privati per calcoli tecnici
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcola RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi.iloc[-1], 2) if not rsi.empty else 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> tuple:
        """Calcola MACD"""
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return (
            round(macd.iloc[-1], 4),
            round(signal.iloc[-1], 4),
            round(histogram.iloc[-1], 4)
        )
    
    def _calculate_bollinger_bands(self, prices: pd.Series, 
                                   period: int = 20, std_dev: int = 2) -> tuple:
        """Calcola Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return (
            round(upper.iloc[-1], 2),
            round(sma.iloc[-1], 2),
            round(lower.iloc[-1], 2)
        )
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, 
                      close: pd.Series, period: int = 14) -> float:
        """Calcola Average True Range"""
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return round(atr.iloc[-1], 4) if not atr.empty else 0.0