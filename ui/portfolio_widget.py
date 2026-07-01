"""
Widget Portfolio - Gestione e visualizzazione posizioni
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QComboBox, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QMenu, QCheckBox
)
from PySide6.QtCore import Qt, Signal, Slot, QPoint
from PySide6.QtGui import QColor, QFont, QAction, QBrush
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio

from loguru import logger


class AddPositionDialog(QDialog):
    """Dialog per aggiungere una nuova posizione"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Posizione")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.asset_input = QLineEdit()
        self.asset_input.setPlaceholderText("Es: AAPL, BTC-USD")
        layout.addRow("Asset:", self.asset_input)
        
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantità")
        layout.addRow("Quantità:", self.quantity_input)
        
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Prezzo di acquisto")
        layout.addRow("Prezzo Acquisto:", self.price_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["stock", "crypto", "etf", "forex"])
        layout.addRow("Tipo:", self.type_combo)
        
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["paper_trading", "interactive_brokers", "binance"])
        layout.addRow("Broker:", self.broker_combo)
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Note opzionali")
        layout.addRow("Note:", self.notes_input)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Ottiene i dati inseriti"""
        return {
            "asset": self.asset_input.text().upper(),
            "quantity": float(self.quantity_input.text() or 0),
            "entry_price": float(self.price_input.text() or 0),
            "asset_type": self.type_combo.currentText(),
            "broker": self.broker_combo.currentText(),
            "notes": self.notes_input.text()
        }


class PortfolioWidget(QWidget):
    """Widget gestione portafoglio"""
    
    position_closed_signal = Signal(str, float)  # asset, profit
    refresh_needed = Signal()
    
    def __init__(self, engine, container):
        super().__init__()
        self.engine = engine
        self.container = container
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Configura interfaccia"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("💼 Portfolio")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filtri
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tutte le posizioni", "Aperte", "Chiuse"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        header_layout.addWidget(QLabel("Filtra:"))
        header_layout.addWidget(self.filter_combo)
        
        # Pulsanti
        add_btn = QPushButton("➕ Aggiungi Posizione")
        add_btn.clicked.connect(self.add_position)
        header_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("🔄 Aggiorna")
        refresh_btn.clicked.connect(lambda: asyncio.ensure_future(self.refresh()))
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Tabella posizioni
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Asset", "Tipo", "Quantità", "Prezzo Acquisto",
            "Prezzo Corrente", "Valore", "P&L €",
            "P&L %", "Stop Loss", "Data Apertura", "Azioni"
        ])
        
        # Configura tabella
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
        # Riepilogo
        summary_layout = QHBoxLayout()
        
        self.summary_label = QLabel(
            "Posizioni aperte: 0 | Valore totale: €0.00 | P&L: €0.00 (0.00%)"
        )
        self.summary_label.setStyleSheet("font-weight: bold; padding: 5px;")
        summary_layout.addWidget(self.summary_label)
        
        layout.addLayout(summary_layout)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connetti segnali"""
        self.refresh_needed.connect(lambda: asyncio.ensure_future(self.refresh()))
    
    async def refresh(self):
        """Aggiorna la tabella del portfolio"""
        try:
            summary = await self.engine.get_portfolio_summary()
            holdings = summary.get("holdings", [])
            
            # Filtra in base alla selezione
            filter_text = self.filter_combo.currentText()
            if filter_text == "Aperte":
                holdings = [h for h in holdings if h.get("status") == "open"]
            elif filter_text == "Chiuse":
                holdings = [h for h in holdings if h.get("status") == "closed"]
            
            # Popola tabella
            self.table.setRowCount(len(holdings))
            
            for row, holding in enumerate(holdings):
                self._populate_row(row, holding)
            
            # Aggiorna riepilogo
            open_count = summary.get("open_positions", 0)
            total_value = summary.get("total_value", 0)
            total_pnl = summary.get("total_pnl_eur", 0)
            total_pnl_pct = summary.get("total_pnl_pct", 0)
            
            self.summary_label.setText(
                f"Posizioni aperte: {open_count} | "
                f"Valore totale: €{total_value:,.2f} | "
                f"P&L: €{total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)"
            )
            
        except Exception as e:
            logger.error(f"Errore refresh portfolio: {e}")
    
    def _populate_row(self, row: int, holding: Dict[str, Any]):
        """Popola una riga della tabella"""
        # Asset
        self.table.setItem(row, 0, QTableWidgetItem(holding.get("asset", "")))
        
        # Tipo
        self.table.setItem(row, 1, QTableWidgetItem(holding.get("asset_type", "")))
        
        # Quantità
        qty_item = QTableWidgetItem(f"{holding.get('quantity', 0):.4f}")
        qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 2, qty_item)
        
        # Prezzo acquisto
        entry_item = QTableWidgetItem(f"€{holding.get('entry_price', 0):.2f}")
        entry_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 3, entry_item)
        
        # Prezzo corrente
        current_price = holding.get("current_price")
        if current_price:
            current_item = QTableWidgetItem(f"€{current_price:.2f}")
        else:
            current_item = QTableWidgetItem("N/D")
        current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 4, current_item)
        
        # Valore
        value = holding.get("current_price", 0) * holding.get("quantity", 0)
        value_item = QTableWidgetItem(f"€{value:,.2f}")
        value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 5, value_item)
        
        # P&L €
        pnl_eur = holding.get("profit_eur", 0)
        pnl_item = QTableWidgetItem(f"€{pnl_eur:+,.2f}")
        pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pnl_item.setForeground(QBrush(QColor("#28a745" if pnl_eur >= 0 else "#dc3545")))
        self.table.setItem(row, 6, pnl_item)
        
        # P&L %
        pnl_pct = holding.get("profit_pct", 0)
        pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
        pnl_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pnl_pct_item.setForeground(QBrush(QColor("#28a745" if pnl_pct >= 0 else "#dc3545")))
        self.table.setItem(row, 7, pnl_pct_item)
        
        # Stop Loss
        sl = holding.get("stop_loss", "-")
        self.table.setItem(row, 8, QTableWidgetItem(str(sl)))
        
        # Data apertura
        open_date = holding.get("open_date", "")
        if open_date:
            try:
                date_obj = datetime.fromisoformat(open_date)
                date_str = date_obj.strftime("%d/%m/%Y %H:%M")
            except:
                date_str = open_date
        else:
            date_str = ""
        self.table.setItem(row, 9, QTableWidgetItem(date_str))
        
        # Pulsanti azioni (solo per posizioni aperte)
        if holding.get("status") == "open":
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            analyze_btn = QPushButton("🤖 Analizza")
            analyze_btn.setFixedSize(80, 25)
            analyze_btn.clicked.connect(
                lambda checked, h=holding: self.analyze_position(h)
            )
            actions_layout.addWidget(analyze_btn)
            
            close_btn = QPushButton("💰 Chiudi")
            close_btn.setFixedSize(80, 25)
            close_btn.setStyleSheet("background-color: #dc3545; color: white;")
            close_btn.clicked.connect(
                lambda checked, h=holding: self.close_position(h)
            )
            actions_layout.addWidget(close_btn)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 10, actions_widget)
    
    def apply_filter(self, filter_text: str):
        """Applica filtro alla tabella"""
        self.refresh_needed.emit()
    
    def add_position(self):
        """Aggiunge una nuova posizione"""
        dialog = AddPositionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            
            if data["asset"] and data["quantity"] > 0 and data["entry_price"] > 0:
                asyncio.ensure_future(self._add_position_async(data))
            else:
                QMessageBox.warning(self, "Dati non validi", 
                                   "Compila tutti i campi correttamente")
    
    async def _add_position_async(self, data: Dict[str, Any]):
        """Aggiunge posizione in modo asincrono"""
        try:
            await self.container.portfolio_manager.add_position(
                asset=data["asset"],
                quantity=data["quantity"],
                entry_price=data["entry_price"],
                asset_type=data["asset_type"],
                broker=data["broker"],
                notes=data["notes"]
            )
            
            QMessageBox.information(self, "Posizione Aggiunta",
                                   f"Posizione {data['asset']} aggiunta con successo")
            self.refresh_needed.emit()
            
        except Exception as e:
            logger.error(f"Errore aggiunta posizione: {e}")
            QMessageBox.critical(self, "Errore", f"Impossibile aggiungere posizione: {e}")
    
    def analyze_position(self, holding: Dict[str, Any]):
        """Richiede analisi AI per una posizione"""
        holding_id = holding.get("id")
        if holding_id:
            asyncio.ensure_future(self._analyze_async(holding_id))
    
    async def _analyze_async(self, holding_id: int):
        """Analisi asincrona posizione"""
        try:
            result = await self.engine.analyze_single_position(holding_id)
            if result:
                msg = (
                    f"Analisi completata:\n\n"
                    f"Decisione: {result['decision']}\n"
                    f"Probabilità: {result['probability']}%\n"
                    f"Rischio: {result['risk_level']}\n\n"
                    f"Motivazione: {result['motivation'][:200]}..."
                )
                QMessageBox.information(self, "Analisi AI", msg)
        except Exception as e:
            logger.error(f"Errore analisi posizione: {e}")
            QMessageBox.critical(self, "Errore", str(e))
    
    def close_position(self, holding: Dict[str, Any]):
        """Chiude una posizione"""
        reply = QMessageBox.question(
            self,
            "Conferma Chiusura",
            f"Vuoi chiudere la posizione {holding['asset']}?\n\n"
            f"Quantità: {holding['quantity']}\n"
            f"P&L: €{holding.get('profit_eur', 0):+,.2f} ({holding.get('profit_pct', 0):+.2f}%)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            asyncio.ensure_future(self._close_position_async(holding))
    
    async def _close_position_async(self, holding: Dict[str, Any]):
        """Chiusura asincrona posizione"""
        try:
            result = await self.container.portfolio_manager.close_position(
                holding_id=holding["id"],
                exit_price=holding.get("current_price", holding["entry_price"]),
                exit_reason="manual"
            )
            
            self.position_closed_signal.emit(
                holding["asset"],
                holding.get("profit_eur", 0)
            )
            
            QMessageBox.information(
                self,
                "Posizione Chiusa",
                f"Posizione {holding['asset']} chiusa.\n"
                f"P&L realizzato: €{holding.get('profit_eur', 0):+,.2f}"
            )
            
            self.refresh_needed.emit()
            
        except Exception as e:
            logger.error(f"Errore chiusura posizione: {e}")
            QMessageBox.critical(self, "Errore", str(e))
    
    def show_context_menu(self, position: QPoint):
        """Mostra menu contestuale"""
        menu = QMenu()
        
        analyze_action = QAction("🤖 Analizza con AI", self)
        analyze_action.triggered.connect(
            lambda: self._context_analyze()
        )
        menu.addAction(analyze_action)
        
        menu.addSeparator()
        
        edit_action = QAction("✏️ Modifica", self)
        menu.addAction(edit_action)
        
        close_action = QAction("💰 Chiudi Posizione", self)
        close_action.triggered.connect(
            lambda: self._context_close()
        )
        menu.addAction(close_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Elimina", self)
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def _context_analyze(self):
        """Analizza posizione dal menu contestuale"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            asset = self.table.item(current_row, 0).text()
            # Trova holding nel database e analizza
            logger.info(f"Analisi richiesta per: {asset}")
    
    def _context_close(self):
        """Chiudi posizione dal menu contestuale"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            asset = self.table.item(current_row, 0).text()
            # Implementa chiusura
            logger.info(f"Chiusura richiesta per: {asset}")