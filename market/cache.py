"""
Cache per dati di mercato
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio

from loguru import logger


class MarketDataCache:
    """Cache in memoria con TTL per dati di mercato"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        """
        Inizializza cache
        
        Args:
            max_size: Dimensione massima cache
            default_ttl: TTL predefinito in secondi
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._lock = asyncio.Lock()
        
        logger.info(f"MarketDataCache inizializzata: size={max_size}, ttl={default_ttl}s")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Ottiene valore dalla cache
        
        Args:
            key: Chiave cache
            
        Returns:
            Valore o None se scaduto/non presente
        """
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Verifica TTL
            if datetime.now() > entry["expires_at"]:
                del self._cache[key]
                return None
            
            # Sposta in fondo (LRU)
            self._cache.move_to_end(key)
            
            return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Salva valore in cache
        
        Args:
            key: Chiave
            value: Valore
            ttl: TTL in secondi (usa default se None)
        """
        async with self._lock:
            # Verifica dimensione
            if len(self._cache) >= self.max_size:
                # Rimuovi elemento più vecchio (LRU)
                self._cache.popitem(last=False)
            
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            
            self._cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
                "created_at": datetime.now()
            }
    
    async def delete(self, key: str):
        """Rimuove elemento dalla cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self):
        """Pulisce tutta la cache"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache pulita")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche cache"""
        async with self._lock:
            total = len(self._cache)
            expired = sum(
                1 for entry in self._cache.values() 
                if datetime.now() > entry["expires_at"]
            )
            
            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "max_size": self.max_size,
                "usage_pct": (total / self.max_size * 100) if self.max_size > 0 else 0
            }
    
    async def cleanup_expired(self):
        """Rimuove elementi scaduti"""
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry["expires_at"]
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Rimossi {len(expired_keys)} elementi scaduti dalla cache")