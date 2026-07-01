"""
Widget Notifiche - Visualizzazione e gestione notifiche
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QCheckBox,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QColor, QBrush
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

from loguru import logger


class NotificationsWidget(QWidget):
    """Widget gestione notifiche"""
    
    notification_clicked = Signal(dict)
    clear_requested = Signal()
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.notifications: List[Dict] = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Timer refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(lambda: asyncio.ensure_future(self.refresh()))
        self.refresh_timer.start(15000)  # 15 secondi
    
    def setup_ui(self):
        """Configura interfaccia"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔔 Centro Notifiche")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filtri
        self.filter_group = QGroupBox("Filtri")
        filter_layout = QHBoxLayout()
        
        self.show_info_cb = QCheckBox("Info")
        self.show_info_cb.setChecked(True)
        self.show_info_cb.toggled.connect(self.apply_filters)
        filter_layout.addWidget(self.show_info_cb)
        
        self.show_alerts_cb = QCheckBox("Alert")
        self.show_alerts_cb.setChecked(True)
        self.show_alerts_cb.toggled.connect(self.apply_filters)
        filter_layout.addWidget(self.show_alerts_cb)
        
        self.show_ai_cb = QCheckBox("AI")
        self.show_ai_cb.setChecked(True)
        self.show_ai_cb.toggled.connect(self.apply_filters)
        filter_layout.addWidget(self.show_ai_cb)
        
        self.show_trades_cb = QCheckBox("Trade")
        self.show_trades_cb.setChecked(True)
        self.show_trades_cb.toggled.connect(self.apply_filters)
        filter_layout.addWidget(self.show_trades_cb)
        
        self.filter_group.setLayout(filter_layout)
        header_layout.addWidget(self.filter_group)
        
        layout.addLayout(header_layout)
        
        # Lista notifiche
        self.notifications_list = QListWidget()
        self.notifications_list.setAlternatingRowColors(True)
        self.notifications_list.itemClicked.connect(self.on_notification_clicked)
        self.notifications_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.notifications_list)
        
        # Controlli
        controls_layout = QHBoxLayout()
        
        self.unread_count_label = QLabel("Notifiche non lette: 0")
        controls_layout.addWidget(self.unread_count_label)
        
        controls_layout.addStretch()
        
        mark_all_btn = QPushButton("✓ Segna tutte come lette")
        mark_all_btn.clicked.connect(self.mark_all_read)
        controls_layout.addWidget(mark_all_btn)
        
        clear_btn = QPushButton("🗑 Pulisci Notifiche")
        clear_btn.clicked.connect(self.clear_notifications)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        controls_layout.addWidget(clear_btn)
        
        layout.addLayout(controls_layout)
        
        # Dettaglio notifica
        detail_group = QGroupBox("Dettaglio Notifica")
        detail_layout = QVBoxLayout()
        
        self.detail_title = QLabel("Seleziona una notifica")
        self.detail_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        detail_layout.addWidget(self.detail_title)
        
        self.detail_message = QLabel("")
        self.detail_message.setWordWrap(True)
        detail_layout.addWidget(self.detail_message)
        
        self.detail_time = QLabel("")
        self.detail_time.setStyleSheet("color: #666; font-size: 11px;")
        detail_layout.addWidget(self.detail_time)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connetti segnali"""
        self.clear_requested.connect(self._on_clear)
    
    async def refresh(self):
        """Aggiorna lista notifiche"""
        try:
            # Qui andrebbe la chiamata al database per recuperare notifiche
            # Per ora usiamo dati di esempio
            self.notifications = await self._get_notifications()
            self.populate_list()
        except Exception as e:
            logger.error(f"Errore refresh notifiche: {e}")
    
    async def _get_notifications(self) -> List[Dict]:
        """Recupera notifiche dal database"""
        # Implementare recupero dal database
        return []
    
    def populate_list(self):
        """Popola la lista notifiche"""
        self.notifications_list.clear()
        
        filtered_notifications = self._filter_notifications(self.notifications)
        
        unread_count = 0
        
        for notification in filtered_notifications:
            # Crea item
            item = QListWidgetItem()
            
            # Formatta titolo
            display_text = f"{notification.get('type', '').upper()}: {notification.get('title', '')}"
            
            # Aggiungi icona in base al tipo
            icon_map = {
                "info": "ℹ️",
                "alert": "⚠️",
                "trade": "💰",
                "ai_suggestion": "🤖",
                "performance": "📈",
                "error": "❌"
            }
            
            icon = icon_map.get(notification.get("type", "info"), "📌")
            item.setText(f"{icon} {display_text}")
            
            # Colore in base all'urgenza
            if notification.get("urgent"):
                item.setBackground(QBrush(QColor("#fff3cd")))
            
            # Tooltip con messaggio completo
            item.setToolTip(notification.get("message", ""))
            
            # Salva dati notifica
            item.setData(Qt.UserRole, notification)
            
            self.notifications_list.addItem(item)
            
            if not notification.get("acknowledged", False):
                unread_count += 1
        
        self.unread_count_label.setText(f"Notifiche non lette: {unread_count}")
    
    def _filter_notifications(self, notifications: List[Dict]) -> List[Dict]:
        """Filtra notifiche in base ai checkbox"""
        filtered = []
        
        for notification in notifications:
            notif_type = notification.get("type", "")
            
            if notif_type == "info" and not self.show_info_cb.isChecked():
                continue
            if notif_type == "alert" and not self.show_alerts_cb.isChecked():
                continue
            if notif_type == "ai_suggestion" and not self.show_ai_cb.isChecked():
                continue
            if notif_type == "trade" and not self.show_trades_cb.isChecked():
                continue
            
            filtered.append(notification)
        
        return filtered
    
    def apply_filters(self):
        """Applica filtri"""
        self.populate_list()
    
    def on_notification_clicked(self, item: QListWidgetItem):
        """Gestisce click su notifica"""
        notification = item.data(Qt.UserRole)
        
        if notification:
            # Aggiorna dettaglio
            self.detail_title.setText(notification.get("title", ""))
            self.detail_message.setText(notification.get("message", ""))
            
            timestamp = notification.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    time_str = str(timestamp)
                self.detail_time.setText(f"Ricevuta: {time_str}")
            
            # Emetti segnale
            self.notification_clicked.emit(notification)
            
            # Segna come letta
            if not notification.get("acknowledged"):
                notification["acknowledged"] = True
                item.setBackground(QBrush(QColor("white")))
                
                # Aggiorna database
                asyncio.ensure_future(self._mark_as_read(notification.get("id")))
    
    async def _mark_as_read(self, notification_id: int):
        """Segna notifica come letta nel database"""
        try:
            # Implementare aggiornamento database
            logger.debug(f"Notifica {notification_id} segnata come letta")
        except Exception as e:
            logger.error(f"Errore marcatura notifica: {e}")
    
    def mark_all_read(self):
        """Segna tutte le notifiche come lette"""
        for i in range(self.notifications_list.count()):
            item = self.notifications_list.item(i)
            notification = item.data(Qt.UserRole)
            
            if notification and not notification.get("acknowledged"):
                notification["acknowledged"] = True
                item.setBackground(QBrush(QColor("white")))
        
        self.unread_count_label.setText("Notifiche non lette: 0")
        logger.info("Tutte le notifiche segnate come lette")
    
    def clear_notifications(self):
        """Pulisce tutte le notifiche"""
        self.notifications_list.clear()
        self.notifications.clear()
        self.detail_title.setText("Seleziona una notifica")
        self.detail_message.setText("")
        self.detail_time.setText("")
        self.clear_requested.emit()
    
    @Slot()
    def _on_clear(self):
        """Callback pulizia notifiche"""
        logger.info("Notifiche pulite")
    
    def add_notification(self, notification: Dict):
        """Aggiunge una nuova notifica"""
        self.notifications.insert(0, notification)
        self.populate_list()