"""
Modelli SQLAlchemy per il database
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, 
    Boolean, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Configurazione utente"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, default="default")
    default_broker = Column(String(50), default="paper_trading")
    default_ai = Column(String(50), default="openai")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PortfolioHolding(Base):
    """Posizioni nel portafoglio"""
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String(20), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), default="stock")  # stock, crypto, etf, forex
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    broker = Column(String(50), default="paper_trading")
    status = Column(String(20), default="open", index=True)  # open, closed, pending
    
    # Date
    open_date = Column(DateTime, default=func.now())
    close_date = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Risk management
    stop_loss = Column(Float, nullable=True)  # Percentuale o prezzo
    take_profit = Column(Float, nullable=True)
    position_size_pct = Column(Float, default=100.0)  # Percentuale della posizione
    
    # Metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Lista di tag
    ai_analysis_count = Column(Integer, default=0)
    
    def calculate_profit_eur(self) -> float:
        """Calcola profitto in EUR"""
        if self.current_price and self.entry_price:
            return (self.current_price - self.entry_price) * self.quantity - self.commission
        return 0.0
    
    def calculate_profit_percentage(self) -> float:
        """Calcola profitto in percentuale"""
        if self.current_price and self.entry_price and self.entry_price > 0:
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        return 0.0
    
    def to_dict(self) -> dict:
        """Converte in dizionario"""
        return {
            "id": self.id,
            "asset": self.asset,
            "symbol": self.symbol,
            "asset_type": self.asset_type,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "profit_eur": self.calculate_profit_eur(),
            "profit_pct": self.calculate_profit_percentage(),
            "commission": self.commission,
            "status": self.status,
            "open_date": self.open_date.isoformat() if self.open_date else None,
            "close_date": self.close_date.isoformat() if self.close_date else None,
            "broker": self.broker,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "notes": self.notes
        }


class ClosedTrade(Base):
    """Trade chiusi/archiviati"""
    __tablename__ = "closed_trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), default="stock")
    quantity = Column(Float, nullable=False)
    
    # Prezzi
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    
    # Performance
    pnl_eur = Column(Float, nullable=False)
    pnl_pct = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    
    # Date
    open_date = Column(DateTime, nullable=False)
    close_date = Column(DateTime, default=func.now())
    holding_period_days = Column(Integer)
    
    # Decisioni
    broker = Column(String(50))
    ai_decision = Column(String(50))  # SELL, REDUCE, etc.
    exit_reason = Column(String(100))  # manual, stop_loss, take_profit, ai_suggestion
    
    # Analisi post-trade
    trade_quality = Column(String(20))  # excellent, good, average, poor
    ai_post_analysis = Column(Text)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> dict:
        """Converte in dizionario"""
        return {
            "id": self.id,
            "asset": self.asset,
            "pnl_eur": self.pnl_eur,
            "pnl_pct": self.pnl_pct,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "open_date": self.open_date.isoformat(),
            "close_date": self.close_date.isoformat(),
            "trade_quality": self.trade_quality,
            "exit_reason": self.exit_reason
        }


class AnalysisHistory(Base):
    """Storico analisi AI"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    # Riferimento posizione
    holding_id = Column(Integer, ForeignKey("portfolio_holdings.id"), nullable=True)
    holding = relationship("PortfolioHolding", backref="analyses")
    
    # Provider AI
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    
    # Prompt e risposta
    request_prompt = Column(Text)
    response_raw = Column(Text)
    response_json = Column(JSON)
    
    # Decisione AI
    decision = Column(String(30))  # HOLD, BUY, SELL, REDUCE_POSITION, INCREASE_POSITION
    probability = Column(Float)
    risk_level = Column(String(20))  # low, medium, high, very_high
    
    # Dettagli analisi
    motivation = Column(Text)
    strengths = Column(JSON)  # Lista punti di forza
    weaknesses = Column(JSON)  # Lista punti di debolezza
    targets = Column(JSON)  # Lista target prices
    stop_loss_suggested = Column(Float)
    
    # Performance
    execution_time_ms = Column(Float)  # Tempo esecuzione richiesta AI
    token_count = Column(Integer)  # Token utilizzati
    
    def to_dict(self) -> dict:
        """Converte in dizionario"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "decision": self.decision,
            "probability": self.probability,
            "risk_level": self.risk_level,
            "motivation": self.motivation,
            "targets": self.targets,
            "stop_loss_suggested": self.stop_loss_suggested
        }


class Notification(Base):
    """Notifiche di sistema"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    type = Column(String(30))  # info, alert, trade, ai_suggestion, performance, error
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    urgent = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Metadati
    related_asset = Column(String(20), nullable=True)
    action_taken = Column(String(50), nullable=True)
    
    def to_dict(self) -> dict:
        """Converte in dizionario"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "urgent": self.urgent,
            "acknowledged": self.acknowledged,
            "related_asset": self.related_asset
        }


class ConversationMessage(Base):
    """Messaggi conversazione AI"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    session_id = Column(String(100), index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Contesto
    context_type = Column(String(30))  # general, portfolio_analysis, trade_suggestion
    related_asset = Column(String(20), nullable=True)
    
    def to_dict(self) -> dict:
        """Converte in dizionario"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "context_type": self.context_type
        }


class Settings(Base):
    """Impostazioni applicazione"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    type = Column(String(20), default="str")  # str, int, float, bool, json
    description = Column(String(500))
    category = Column(String(50))  # ai, broker, ui, notifications, etc.
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def get_value(self):
        """Converte il valore nel tipo corretto"""
        if self.type == "int":
            return int(self.value)
        elif self.type == "float":
            return float(self.value)
        elif self.type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        elif self.type == "json":
            import json
            return json.loads(self.value)
        return self.value


class PerformanceMetrics(Base):
    """Metriche di performance"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=func.now(), index=True)
    
    # Portfolio value
    total_value = Column(Float)
    cash_balance = Column(Float, default=0.0)
    invested_value = Column(Float)
    
    # Performance
    daily_pnl_eur = Column(Float, default=0.0)
    daily_pnl_pct = Column(Float, default=0.0)
    total_pnl_eur = Column(Float, default=0.0)
    total_pnl_pct = Column(Float, default=0.0)
    
    # Risk metrics
    drawdown_pct = Column(Float)
    sharpe_ratio = Column(Float)
    volatility = Column(Float)
    
    # Trades
    open_positions_count = Column(Integer, default=0)
    closed_trades_today = Column(Integer, default=0)
    win_rate = Column(Float)  # Percentuale trade vincenti
    
    def to_dict(self) -> dict:
        """Converte in dizionario"""
        return {
            "date": self.date.isoformat(),
            "total_value": self.total_value,
            "daily_pnl_eur": self.daily_pnl_eur,
            "daily_pnl_pct": self.daily_pnl_pct,
            "drawdown_pct": self.drawdown_pct,
            "open_positions": self.open_positions_count
        }