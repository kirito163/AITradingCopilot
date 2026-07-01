"""
Widget Conversazione AI - Chat interattiva con l'assistente
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QScrollArea, QFrame,
    QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor, QTextCursor
from datetime import datetime
from typing import List, Dict
import asyncio

from loguru import logger


class ChatBubble(QFrame):
    """Bolla di chat per messaggi"""
    
    def __init__(self, message: str, is_user: bool = False, timestamp: str = ""):
        super().__init__()
        
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        
        # Colori diversi per utente e AI
        if is_user:
            bg_color = "#0078d7"
            text_color = "white"
            align = Qt.AlignRight
        else:
            bg_color = "#f0f0f0"
            text_color = "#333"
            align = Qt.AlignLeft
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Tu" if is_user else "🤖 AI Assistant")
        header.setStyleSheet(f"font-weight: bold; color: {text_color}; font-size: 11px;")
        header.setAlignment(align)
        layout.addWidget(header)
        
        # Messaggio
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
        msg_label.setAlignment(align)
        layout.addWidget(msg_label)
        
        # Timestamp
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(f"color: {text_color}; font-size: 9px;")
            time_label.setAlignment(align)
            layout.addWidget(time_label)
        
        self.setLayout(layout)


class AIConversationWidget(QWidget):
    """Widget conversazione con AI"""
    
    message_sent = Signal(str)
    response_received = Signal(str, dict)  # message, metadata
    
    def __init__(self, engine, container):
        super().__init__()
        self.engine = engine
        self.container = container
        self.conversation_history: List[Dict] = []
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Configura interfaccia chat"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🤖 AI Trading Assistant")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Controlli conversazione
        self.context_combo = QComboBox()
        self.context_combo.addItems([
            "Generale",
            "Analisi Portafoglio",
            "Ricerca Opportunità",
            "Analisi Tecnica",
            "Gestione Rischio"
        ])
        header_layout.addWidget(QLabel("Contesto:"))
        header_layout.addWidget(self.context_combo)
        
        clear_btn = QPushButton("🗑 Pulisci Chat")
        clear_btn.clicked.connect(self.clear_chat)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Area chat scrollabile
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_container.setLayout(self.chat_layout)
        
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)
        
        # Area input
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText(
            "Scrivi un messaggio... (es: 'Analizza il mio portafoglio', 'Cerca nuove opportunità')"
        )
        self.message_input.setMaximumHeight(80)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #0078d7;
            }
        """)
        input_layout.addWidget(self.message_input)
        
        # Pulsanti azione
        button_layout = QVBoxLayout()
        
        self.send_btn = QPushButton("📤 Invia")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        button_layout.addWidget(self.send_btn)
        
        self.voice_btn = QPushButton("🎤 Parla")
        self.voice_btn.clicked.connect(self.start_voice_input)
        self.voice_btn.setEnabled(False)  # Da abilitare quando STT è configurato
        button_layout.addWidget(self.voice_btn)
        
        input_layout.addLayout(button_layout)
        
        layout.addLayout(input_layout)
        
        # Pulsanti azioni rapide
        quick_actions_layout = QHBoxLayout()
        
        actions = [
            ("📊 Analizza Portafoglio", "Analizza il mio portafoglio attuale"),
            ("🔍 Cerca Opportunità", "Cerca nuove opportunità di investimento"),
            ("📈 Analisi Tecnica", "Fai un'analisi tecnica delle mie posizioni"),
            ("⚠️ Valuta Rischi", "Valuta i rischi del mio portafoglio"),
            ("📝 Riepilogo", "Fammi un riepilogo delle performance")
        ]
        
        for label, message in actions:
            btn = QPushButton(label)
            btn.setMaximumWidth(150)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            btn.clicked.connect(lambda checked, m=message: self.send_quick_action(m))
            quick_actions_layout.addWidget(btn)
        
        layout.addLayout(quick_actions_layout)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connetti segnali"""
        self.message_sent.connect(self._on_message_sent)
        self.response_received.connect(self._on_response_received)
        
        # Shortcut per invio
        self.message_input.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filtra eventi per shortcut"""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent
        
        if obj == self.message_input and event.type() == QEvent.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key_Return and key_event.modifiers() == Qt.NoModifier:
                self.send_message()
                return True
            elif key_event.key() == Qt.Key_Return and key_event.modifiers() == Qt.ShiftModifier:
                # Nuova linea
                return False
        
        return super().eventFilter(obj, event)
    
    def send_message(self):
        """Invia messaggio"""
        message = self.message_input.toPlainText().strip()
        if message:
            # Aggiungi messaggio utente alla chat
            self.add_message(message, is_user=True)
            
            # Pulisci input
            self.message_input.clear()
            
            # Invia all'AI
            asyncio.ensure_future(self._process_message(message))
    
    def send_quick_action(self, message: str):
        """Invia azione rapida"""
        self.message_input.setText(message)
        self.send_message()
    
    async def _process_message(self, message: str):
        """Processa messaggio con AI"""
        try:
            # Costruisci contesto
            context = self.context_combo.currentText()
            
            # Ottieni provider AI
            ai_provider = self.container.ai_provider
            
            # Prepara prompt di sistema
            system_prompt = self._get_system_prompt(context)
            
            # Ottieni risposta AI
            response = await ai_provider.generate_text(
                prompt=message,
                system=system_prompt
            )
            
            # Aggiungi risposta alla chat
            self.add_message(response, is_user=False)
            
            # Salva conversazione
            self._save_conversation(message, response)
            
        except Exception as e:
            logger.error(f"Errore processamento messaggio: {e}")
            self.add_message(
                f"Mi dispiace, si è verificato un errore: {str(e)}",
                is_user=False
            )
    
    def _get_system_prompt(self, context: str) -> str:
        """Ottiene prompt di sistema basato sul contesto"""
        base_prompt = (
            "Sei un assistente esperto di trading e investimenti. "
            "Fornisci analisi accurate, suggerimenti e spiegazioni dettagliate. "
            "Non dare consigli finanziari definitivi ma analisi informative."
        )
        
        context_prompts = {
            "Analisi Portafoglio": (
                f"{base_prompt}\n"
                f"Contesto: Stai analizzando il portafoglio dell'utente.\n"
                f"Dati portfolio: {self._get_portfolio_context()}"
            ),
            "Ricerca Opportunità": (
                f"{base_prompt}\n"
                "Contesto: Stai cercando nuove opportunità di investimento."
            ),
            "Analisi Tecnica": (
                f"{base_prompt}\n"
                "Contesto: Stai facendo analisi tecnica delle posizioni."
            ),
            "Gestione Rischio": (
                f"{base_prompt}\n"
                "Contesto: Stai valutando la gestione del rischio."
            )
        }
        
        return context_prompts.get(context, base_prompt)
    
    def _get_portfolio_context(self) -> str:
        """Ottiene contesto portfolio per il prompt"""
        try:
            # Qui andrebbe chiamato il portfolio manager per dati reali
            return "Portfolio con posizioni in vari asset."
        except:
            return "Dati portfolio non disponibili."
    
    def add_message(self, message: str, is_user: bool = False):
        """Aggiunge un messaggio alla chat"""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Crea bolla chat
        bubble = ChatBubble(message, is_user, timestamp)
        
        # Aggiungi al layout
        self.chat_layout.addWidget(bubble)
        
        # Scroll in fondo
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scrolla in fondo alla chat"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """Pulisce la chat"""
        # Rimuovi tutti i widget dal layout
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Nuovo session ID
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history.clear()
    
    def start_voice_input(self):
        """Avvia input vocale"""
        if self.container.stt_provider:
            # Implementazione input vocale
            logger.info("Input vocale avviato")
        else:
            logger.warning("STT non configurato")
    
    @Slot(str)
    def _on_message_sent(self, message: str):
        """Callback messaggio inviato"""
        logger.debug(f"Messaggio inviato: {message[:50]}...")
    
    @Slot(str, dict)
    def _on_response_received(self, response: str, metadata: dict):
        """Callback risposta ricevuta"""
        logger.debug(f"Risposta ricevuta: {response[:50]}...")
    
    def _save_conversation(self, user_message: str, ai_response: str):
        """Salva conversazione nel database"""
        try:
            # Salva nel database tramite container
            logger.debug(f"Conversazione salvata: {len(user_message)} -> {len(ai_response)} chars")
        except Exception as e:
            logger.error(f"Errore salvataggio conversazione: {e}")