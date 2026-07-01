"""
Provider Paper Trading - Simulazione trading
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from loguru import logger

from broker.base import (
    AbstractBroker, Order, OrderType, OrderSide,
    OrderStatus, BrokerPosition, AccountInfo
)


class PaperTradingBroker(AbstractBroker):
    """Broker simulato per paper trading"""
    
    def __init__(self, initial_balance: float = 100000.0, **kwargs):
        super().__init__(api_key=None, secret_key=None, **kwargs)
        
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, BrokerPosition] = {}
        self.orders: List[Order] = []
        self._price_cache: Dict[str, float] = {}
        
        logger.info(f"PaperTrading inizializzato: balance=€{initial_balance:,.2f}")
    
    async def connect(self) -> bool:
        """Connessione simulata"""
        self._connected = True
        logger.info("Paper Trading connesso")
        return True
    
    async def disconnect(self):
        """Disconnessione simulata"""
        self._connected = False
        logger.info("Paper Trading disconnesso")
    
    async def get_account_info(self) -> AccountInfo:
        """Ottiene info account simulato"""
        total_positions_value = sum(
            p.market_value for p in self.positions.values()
        )
        
        equity = self.balance + total_positions_value
        
        return AccountInfo(
            account_id="PAPER-001",
            currency="EUR",
            balance=self.balance,
            equity=equity,
            buying_power=self.balance * 2,  # Margine 2x simulato
            margin_used=total_positions_value,
            margin_available=equity - total_positions_value
        )
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Ottiene posizioni aperte"""
        return list(self.positions.values())
    
    async def place_order(self, order: Order) -> Order:
        """Esegue ordine simulato"""
        try:
            # Genera ID se non presente
            if not order.order_id:
                order.order_id = str(uuid.uuid4())[:8]
            
            # Ottieni prezzo corrente o usa quello specificato
            execution_price = order.price or self._price_cache.get(order.symbol, 100.0)
            
            if order.side == OrderSide.BUY:
                cost = execution_price * order.quantity
                
                if cost > self.balance:
                    order.status = OrderStatus.REJECTED
                    logger.warning(f"Ordine rifiutato: fondi insufficienti (need €{cost:,.2f})")
                else:
                    self.balance -= cost
                    order.status = OrderStatus.FILLED
                    order.filled_quantity = order.quantity
                    order.filled_price = execution_price
                    order.updated_at = datetime.now()
                    
                    # Aggiorna posizione
                    if order.symbol in self.positions:
                        pos = self.positions[order.symbol]
                        total_quantity = pos.quantity + order.quantity
                        pos.average_price = (
                            (pos.average_price * pos.quantity + execution_price * order.quantity) 
                            / total_quantity
                        )
                        pos.quantity = total_quantity
                    else:
                        self.positions[order.symbol] = BrokerPosition(
                            symbol=order.symbol,
                            quantity=order.quantity,
                            average_price=execution_price,
                            current_price=execution_price,
                            market_value=order.quantity * execution_price
                        )
                    
                    logger.info(
                        f"BUY eseguito: {order.symbol} x{order.quantity} @ €{execution_price:.2f}"
                    )
            
            elif order.side == OrderSide.SELL:
                if order.symbol not in self.positions:
                    order.status = OrderStatus.REJECTED
                    logger.warning(f"Ordine rifiutato: nessuna posizione in {order.symbol}")
                elif self.positions[order.symbol].quantity < order.quantity:
                    order.status = OrderStatus.REJECTED
                    logger.warning(f"Ordine rifiutato: quantità insufficiente")
                else:
                    revenue = execution_price * order.quantity
                    self.balance += revenue
                    order.status = OrderStatus.FILLED
                    order.filled_quantity = order.quantity
                    order.filled_price = execution_price
                    order.updated_at = datetime.now()
                    
                    # Aggiorna posizione
                    pos = self.positions[order.symbol]
                    pos.quantity -= order.quantity
                    pos.realized_pnl += (execution_price - pos.average_price) * order.quantity
                    
                    if pos.quantity == 0:
                        del self.positions[order.symbol]
                    
                    logger.info(
                        f"SELL eseguito: {order.symbol} x{order.quantity} @ €{execution_price:.2f}"
                    )
            
            self.orders.append(order)
            return order
            
        except Exception as e:
            logger.error(f"Errore esecuzione ordine: {e}")
            order.status = OrderStatus.REJECTED
            return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancella ordine"""
        for order in self.orders:
            if order.order_id == order_id and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                logger.info(f"Ordine {order_id} cancellato")
                return True
        return False
    
    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Ottiene stato ordine"""
        for order in self.orders:
            if order.order_id == order_id:
                return order.status
        return OrderStatus.REJECTED
    
    async def get_order_history(self, limit: int = 50) -> List[Order]:
        """Ottiene storico ordini"""
        return self.orders[-limit:]
    
    def update_price(self, symbol: str, price: float):
        """Aggiorna prezzo per paper trading"""
        self._price_cache[symbol] = price
        
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = price
            pos.market_value = price * pos.quantity
            pos.unrealized_pnl = (price - pos.average_price) * pos.quantity
    
    def reset_account(self):
        """Resetta account paper trading"""
        self.balance = self.initial_balance
        self.positions.clear()
        self.orders.clear()
        self._price_cache.clear()
        logger.info("Account paper trading resettato")