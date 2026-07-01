"""
Portfolio Manager - Gestione posizioni e calcoli
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, and_
from loguru import logger

from database.models import PortfolioHolding, ClosedTrade, PerformanceMetrics
from database.connection import DatabaseManager


class PortfolioManager:
    """Gestisce operazioni sul portafoglio"""
    
    def __init__(self, database: DatabaseManager, market_data=None):
        """
        Inizializza portfolio manager
        
        Args:
            database: Database manager
            market_data: Provider dati di mercato (opzionale)
        """
        self.db = database
        self.market_data = market_data
        self._initialized = False
        
        logger.info("PortfolioManager creato")
    
    async def initialize(self):
        """Inizializza il manager"""
        self._initialized = True
        logger.info("PortfolioManager inizializzato")
    
    async def add_position(self, asset: str, quantity: float, 
                          entry_price: float, asset_type: str = "stock",
                          broker: str = "paper_trading", 
                          notes: str = "") -> PortfolioHolding:
        """
        Aggiunge una nuova posizione
        
        Args:
            asset: Simbolo asset
            quantity: Quantità
            entry_price: Prezzo di acquisto
            asset_type: Tipo asset
            broker: Broker utilizzato
            notes: Note opzionali
            
        Returns:
            PortfolioHolding creata
        """
        try:
            holding = PortfolioHolding(
                asset=asset,
                symbol=asset,
                asset_type=asset_type,
                quantity=quantity,
                entry_price=entry_price,
                current_price=entry_price,  # Inizialmente uguale a entry
                broker=broker,
                status="open",
                notes=notes,
                open_date=datetime.now(),
                commission=0.0
            )
            
            await self.db.add(holding)
            logger.info(f"Posizione aggiunta: {asset} x{quantity} @ €{entry_price}")
            
            return holding
            
        except Exception as e:
            logger.error(f"Errore aggiunta posizione: {e}")
            raise
    
    async def close_position(self, holding_id: int, exit_price: float,
                            exit_reason: str = "manual") -> Optional[ClosedTrade]:
        """
        Chiude una posizione esistente
        
        Args:
            holding_id: ID posizione
            exit_price: Prezzo di uscita
            exit_reason: Motivo chiusura
            
        Returns:
            ClosedTrade creato
        """
        try:
            # Recupera holding
            holding = await self.get_holding(holding_id)
            
            if not holding:
                raise ValueError(f"Holding {holding_id} non trovata")
            
            if holding.status != "open":
                raise ValueError(f"Holding {holding_id} già chiusa")
            
            # Calcola P&L
            pnl_eur = (exit_price - holding.entry_price) * holding.quantity - holding.commission
            pnl_pct = ((exit_price - holding.entry_price) / holding.entry_price) * 100
            
            # Calcola periodo
            holding_period = (datetime.now() - holding.open_date).days
            
            # Crea trade chiuso
            closed_trade = ClosedTrade(
                asset=holding.asset,
                symbol=holding.symbol,
                asset_type=holding.asset_type,
                quantity=holding.quantity,
                entry_price=holding.entry_price,
                exit_price=exit_price,
                pnl_eur=pnl_eur,
                pnl_pct=pnl_pct,
                commission=holding.commission,
                open_date=holding.open_date,
                close_date=datetime.now(),
                holding_period_days=holding_period,
                broker=holding.broker,
                exit_reason=exit_reason,
                ai_decision=None
            )
            
            # Aggiorna holding
            holding.status = "closed"
            holding.close_date = datetime.now()
            holding.current_price = exit_price
            
            # Salva
            await self.db.add(closed_trade)
            await self.db.add(holding)
            await self.db.commit()
            
            logger.info(
                f"Posizione chiusa: {holding.asset} | "
                f"P&L: €{pnl_eur:+,.2f} ({pnl_pct:+.2f}%) | "
                f"Periodo: {holding_period} giorni"
            )
            
            return closed_trade
            
        except Exception as e:
            logger.error(f"Errore chiusura posizione: {e}")
            raise
    
    async def update_holding(self, holding: PortfolioHolding):
        """Aggiorna una holding nel database"""
        await self.db.add(holding)
        await self.db.commit()
    
    async def update_current_prices(self, market_data=None):
        """
        Aggiorna prezzi correnti di tutte le posizioni aperte
        
        Args:
            market_data: Provider dati di mercato (usa self.market_data se None)
        """
        if market_data is None:
            market_data = self.market_data
        
        if not market_data:
            logger.warning("Nessun provider market data disponibile")
            return
        
        try:
            holdings = await self.get_open_holdings()
            
            for holding in holdings:
                try:
                    price_data = await market_data.get_current_price(holding.asset)
                    if price_data and price_data.price:
                        holding.current_price = price_data.price
                        holding.last_updated = datetime.now()
                        await self.update_holding(holding)
                        logger.debug(f"Prezzo aggiornato: {holding.asset} = {price_data.price}")
                except Exception as e:
                    logger.warning(f"Impossibile aggiornare prezzo {holding.asset}: {e}")
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Errore aggiornamento prezzi: {e}")
    
    async def get_holding(self, holding_id: int) -> Optional[PortfolioHolding]:
        """Recupera una holding per ID"""
        async with await self.db.get_session() as session:
            result = await session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            )
            return result.scalar_one_or_none()
    
    async def get_open_holdings(self) -> List[PortfolioHolding]:
        """Recupera tutte le posizioni aperte"""
        async with await self.db.get_session() as session:
            result = await session.execute(
                select(PortfolioHolding).where(PortfolioHolding.status == "open")
            )
            return result.scalars().all()
    
    async def get_open_assets(self) -> List[str]:
        """Recupera lista asset con posizioni aperte"""
        holdings = await self.get_open_holdings()
        return [h.asset for h in holdings]
    
    async def get_portfolio(self) -> List[PortfolioHolding]:
        """Recupera tutto il portafoglio"""
        async with await self.db.get_session() as session:
            result = await session.execute(select(PortfolioHolding))
            return result.scalars().all()
    
    async def get_closed_trades(self, limit: int = 50) -> List[ClosedTrade]:
        """Recupera trades chiusi recenti"""
        async with await self.db.get_session() as session:
            result = await session.execute(
                select(ClosedTrade)
                .order_by(ClosedTrade.close_date.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_summary(self) -> Dict[str, Any]:
        """
        Calcola riepilogo completo portafoglio
        
        Returns:
            Dizionario con metriche portfolio
        """
        try:
            open_holdings = await self.get_open_holdings()
            closed_trades = await self.get_closed_trades()
            
            # Calcola valori
            total_value = sum(
                (h.current_price or h.entry_price) * h.quantity 
                for h in open_holdings
            )
            
            total_cost = sum(h.entry_price * h.quantity for h in open_holdings)
            total_pnl_eur = total_value - total_cost
            total_pnl_pct = (total_pnl_eur / total_cost * 100) if total_cost > 0 else 0
            
            # P&L giornaliero
            today = datetime.now().date()
            daily_pnl = sum(
                t.pnl_eur for t in closed_trades 
                if t.close_date and t.close_date.date() == today
            )
            
            # Performance storica
            all_trades = closed_trades
            winning_trades = [t for t in all_trades if t.pnl_eur > 0]
            win_rate = (len(winning_trades) / len(all_trades) * 100) if all_trades else 0
            
            # Calcola ROI
            total_invested = total_cost + sum(t.entry_price * t.quantity for t in closed_trades)
            total_returned = total_value + sum(t.exit_price * t.quantity for t in closed_trades)
            roi = ((total_returned - total_invested) / total_invested * 100) if total_invested > 0 else 0
            
            # Drawdown (semplificato)
            drawdown = self._calculate_drawdown(all_trades)
            
            # Volatilità
            volatility = self._calculate_volatility(all_trades)
            
            # Performance per periodo
            performance_week = self._calculate_period_performance(all_trades, 7)
            performance_month = self._calculate_period_performance(all_trades, 30)
            performance_year = self._calculate_period_performance(all_trades, 365)
            
            return {
                "total_value": total_value,
                "total_cost": total_cost,
                "total_pnl_eur": total_pnl_eur,
                "total_pnl_pct": total_pnl_pct,
                "daily_pnl_eur": daily_pnl,
                "daily_pnl_pct": (daily_pnl / total_value * 100) if total_value > 0 else 0,
                "open_positions": len(open_holdings),
                "closed_positions": len(closed_trades),
                "roi": roi,
                "drawdown": drawdown,
                "volatility": volatility,
                "win_rate": win_rate,
                "winning_trades": len(winning_trades),
                "total_trades": len(all_trades),
                "sharpe_ratio": self._calculate_sharpe_ratio(all_trades),
                "holdings": [h.to_dict() for h in open_holdings],
                "recent_trades": [t.to_dict() for t in closed_trades[:10]],
                "performance_week": performance_week,
                "performance_month": performance_month,
                "performance_year": performance_year
            }
            
        except Exception as e:
            logger.error(f"Errore calcolo summary: {e}")
            return self._get_empty_summary()
    
    def _calculate_drawdown(self, trades: List[ClosedTrade]) -> float:
        """Calcola massimo drawdown"""
        if not trades:
            return 0.0
        
        cumulative = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades, key=lambda t: t.close_date or datetime.min):
            cumulative += trade.pnl_eur
            peak = max(peak, cumulative)
            drawdown = (peak - cumulative) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def _calculate_volatility(self, trades: List[ClosedTrade]) -> float:
        """Calcola volatilità (deviazione standard)"""
        if len(trades) < 2:
            return 0.0
        
        pnl_pcts = [t.pnl_pct for t in trades]
        mean = sum(pnl_pcts) / len(pnl_pcts)
        variance = sum((x - mean) ** 2 for x in pnl_pcts) / (len(pnl_pcts) - 1)
        
        return variance ** 0.5
    
    def _calculate_sharpe_ratio(self, trades: List[ClosedTrade], 
                               risk_free_rate: float = 0.02) -> float:
        """Calcola Sharpe Ratio"""
        if len(trades) < 2:
            return 0.0
        
        returns = [t.pnl_pct / 100 for t in trades]
        mean_return = sum(returns) / len(returns)
        std_return = (sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)) ** 0.5
        
        if std_return == 0:
            return 0.0
        
        return (mean_return - risk_free_rate / 365) / std_return
    
    def _calculate_period_performance(self, trades: List[ClosedTrade], 
                                     days: int) -> float:
        """Calcola performance per periodo"""
        cutoff = datetime.now() - timedelta(days=days)
        period_trades = [
            t for t in trades 
            if t.close_date and t.close_date >= cutoff
        ]
        
        if not period_trades:
            return 0.0
        
        return sum(t.pnl_pct for t in period_trades)
    
    def _get_empty_summary(self) -> Dict[str, Any]:
        """Restituisce summary vuoto"""
        return {
            "total_value": 0,
            "total_cost": 0,
            "total_pnl_eur": 0,
            "total_pnl_pct": 0,
            "daily_pnl_eur": 0,
            "daily_pnl_pct": 0,
            "open_positions": 0,
            "closed_positions": 0,
            "roi": 0,
            "drawdown": 0,
            "volatility": 0,
            "win_rate": 0,
            "winning_trades": 0,
            "total_trades": 0,
            "sharpe_ratio": 0,
            "holdings": [],
            "recent_trades": [],
            "performance_week": 0,
            "performance_month": 0,
            "performance_year": 0
        }
    
    async def save_metrics(self):
        """Salva metriche performance correnti"""
        try:
            summary = await self.get_summary()
            
            metrics = PerformanceMetrics(
                date=datetime.now(),
                total_value=summary["total_value"],
                daily_pnl_eur=summary["daily_pnl_eur"],
                daily_pnl_pct=summary["daily_pnl_pct"],
                total_pnl_eur=summary["total_pnl_eur"],
                total_pnl_pct=summary["total_pnl_pct"],
                drawdown_pct=summary["drawdown"],
                sharpe_ratio=summary["sharpe_ratio"],
                volatility=summary["volatility"],
                open_positions_count=summary["open_positions"],
                win_rate=summary["win_rate"]
            )
            
            await self.db.add(metrics)
            logger.info("Metriche performance salvate")
            
        except Exception as e:
            logger.error(f"Errore salvataggio metriche: {e}")