"""
Gestione connessione database con SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import Optional, List, Dict, Any
import asyncio

from loguru import logger

from database.models import Base


class DatabaseManager:
    """Gestisce connessione e operazioni database"""
    
    def __init__(self, database_url: str):
        """
        Inizializza il database manager
        
        Args:
            database_url: URL connessione database
        """
        # Converti sqlite:// in sqlite+aiosqlite:// per async
        if database_url.startswith("sqlite:///"):
            async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            async_url = database_url
            
        self.database_url = database_url
        self.async_database_url = async_url
        
        # Engine sincrono per creazione tabelle
        self.sync_engine = create_engine(database_url, echo=False)
        
        # Engine asincrono per operazioni
        self.async_engine = create_async_engine(
            async_url,
            echo=False,
            future=True
        )
        
        # Session factory asincrona
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(f"DatabaseManager inizializzato: {database_url}")
    
    async def initialize(self):
        """Crea tabelle e inizializza database"""
        try:
            # Crea tutte le tabelle
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Tabelle database create con successo")
            
        except Exception as e:
            logger.error(f"Errore inizializzazione database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """
        Ottieni una sessione asincrona
        
        Returns:
            AsyncSession
        """
        return self.async_session_factory()
    
    async def add(self, obj: Any):
        """Aggiunge un oggetto al database"""
        async with self.async_session_factory() as session:
            session.add(obj)
            await session.commit()
    
    async def add_all(self, objects: List[Any]):
        """Aggiunge multipli oggetti al database"""
        async with self.async_session_factory() as session:
            session.add_all(objects)
            await session.commit()
    
    async def commit(self):
        """Commit delle modifiche"""
        async with self.async_session_factory() as session:
            await session.commit()
    
    async def get_all_settings(self) -> List:
        """Recupera tutte le impostazioni dal database"""
        from database.models import Settings
        
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(select(Settings))
            return result.scalars().all()
    
    async def save_setting(self, key: str, value: Any, type_: str = "str"):
        """Salva o aggiorna un'impostazione"""
        from database.models import Settings
        
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(Settings).where(Settings.key == key)
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = str(value)
            else:
                setting = Settings(key=key, value=str(value), type=type_)
                session.add(setting)
            
            await session.commit()
    
    async def close(self):
        """Chiude connessioni database"""
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        logger.info("Connessioni database chiuse")