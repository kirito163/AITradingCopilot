"""
Finestra principale dell'applicazione
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QLabel, QToolBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from datetime import datetime
import asyncio

from loguru import logger

from ui.dashboard_widget import DashboardWidget
from ui.portfolio_widget import PortfolioWidget
from ui.ai_conversation_widget import AIConversationWidget
from ui.notifications_widget import NotificationsWidget
from ui.settings_dialog import SettingsDialog
from config.settings import settings


class MainWindow(QMainWindow):
    """Finestra principale AI Trading Copilot"""
    
    # Segnali per aggiornamento UI da thread async
    update_status_signal = Signal(str, str)
    update_monitoring_status_signal = Signal(bool, str)
    
    def __init__(self, engine, container):
        """
        Inizializza la finestra principale
        
        Args:
            engine: Istanza CopilotEngine
            container: Container DI
        """
        super().__init__()
        
        self.engine = engine
        self.container = container
        self.settings = settings
        
        self.setWindowTitle(f"AI Trading Copilot v{settings.app_version}")
        self.resize(settings.window_width, settings.window_height)
        
        # Setup UI
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        
        # Connetti segnali
        self._connect_signals()
        
        # Applica tema
        self._apply_theme(settings.theme)
        
        # Timer per aggiornamento periodico UI
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(5000)  # Aggiorna ogni 5 secondi
        
        logger.info("MainWindow inizializzata")
    
    def _setup_menu_bar(self):
        """Configura la barra dei menu"""
        menubar = self.menuBar()
        
        # Menu File
        file_menu = menubar.addMenu("&File")
        
        export_action = QAction("Esporta Dati...", self)
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Esci", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Monitoraggio
        monitor_menu = menubar.addMenu("&Monitoraggio")
        
        start_monitor_action = QAction("Avvia Monitoraggio", self)
        start_monitor_action.triggered.connect(self._start_monitoring)
        monitor_menu.addAction(start_monitor_action)
        
        pause_monitor_action = QAction("Pausa Monitoraggio", self)
        pause_monitor_action.triggered.connect(self._pause_monitoring)
        monitor_menu.addAction(pause_monitor_action)
        
        stop_monitor_action = QAction("Ferma Monitoraggio", self)
        stop_monitor_action.triggered.connect(self._stop_monitoring)
        monitor_menu.addAction(stop_monitor_action)
        
        monitor_menu.addSeparator()
        
        force_check_action = QAction("Forza Controllo Ora", self)
        force_check_action.triggered.connect(self._force_check)
        monitor_menu.addAction(force_check_action)
        
        # Menu Impostazioni
        settings_menu = menubar.addMenu("&Impostazioni")
        
        config_action = QAction("Configurazione...", self)
        config_action.setShortcut("Ctrl+,")
        config_action.triggered.connect(self._open_settings)
        settings_menu.addAction(config_action)
        
        # Menu Aiuto
        help_menu = menubar.addMenu("&Aiuto")
        
        about_action = QAction("Informazioni...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Configura la toolbar"""
        toolbar = QToolBar("Toolbar Principale")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Pulsanti monitoraggio
        self.start_monitor_btn = QAction("▶ Avvia", self)
        self.start_monitor_btn.triggered.connect(self._start_monitoring)
        toolbar.addAction(self.start_monitor_btn)
        
        self.pause_monitor_btn = QAction("⏸ Pausa", self)
        self.pause_monitor_btn.triggered.connect(self._pause_monitoring)
        self.pause_monitor_btn.setEnabled(False)
        toolbar.addAction(self.pause_monitor_btn)
        
        self.stop_monitor_btn = QAction("⏹ Ferma", self)
        self.stop_monitor_btn.triggered.connect(self._stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        toolbar.addAction(self.stop_monitor_btn)
        
        toolbar.addSeparator()
        
        # Pulsante controllo manuale
        check_now_btn = QAction("🔄 Controlla Ora", self)
        check_now_btn.triggered.connect(self._force_check)
        toolbar.addAction(check_now_btn)
        
        toolbar.addSeparator()
        
        # Pulsante impostazioni
        settings_btn = QAction("⚙ Impostazioni", self)
        settings_btn.triggered.connect(self._open_settings)
        toolbar.addAction(settings_btn)
    
    def _setup_central_widget(self):
        """Configura il widget centrale con tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tab widget principale
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tab Dashboard
        self.dashboard_widget = DashboardWidget(self.engine, self.container)
        self.tab_widget.addTab(self.dashboard_widget, "📊 Dashboard")
        
        # Tab Portfolio
        self.portfolio_widget = PortfolioWidget(self.engine, self.container)
        self.tab_widget.addTab(self.portfolio_widget, "💼 Portfolio")
        
        # Tab AI Conversation
        self.ai_widget = AIConversationWidget(self.engine, self.container)
        self.tab_widget.addTab(self.ai_widget, "🤖 AI Assistant")
        
        # Tab Notifiche
        self.notifications_widget = NotificationsWidget(self.container)
        self.tab_widget.addTab(self.notifications_widget, "🔔 Notifiche")
    
    def _setup_status_bar(self):
        """Configura la status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Labels per stato
        self.status_label = QLabel("🟢 Pronto")
        self.status_bar.addWidget(self.status_label)
        
        self.status_bar.addPermanentWidget(QLabel("  |  "))
        
        self.monitor_label = QLabel("Monitoraggio: ⏸ In pausa")
        self.status_bar.addPermanentWidget(self.monitor_label)
        
        self.status_bar.addPermanentWidget(QLabel("  |  "))
        
        self.last_check_label = QLabel("Ultimo controllo: --")
        self.status_bar.addPermanentWidget(self.last_check_label)
        
        self.status_bar.addPermanentWidget(QLabel("  |  "))
        
        self.next_check_label = QLabel("Prossimo controllo: --")
        self.status_bar.addPermanentWidget(self.next_check_label)
    
    def _connect_signals(self):
        """Connetti segnali per aggiornamenti UI"""
        self.update_status_signal.connect(self._on_status_update)
        self.update_monitoring_status_signal.connect(self._on_monitoring_status_update)
    
    @Slot(str, str)
    def _on_status_update(self, status, message):
        """Aggiorna status bar"""
        self.status_label.setText(f"{status} {message}")
    
    @Slot(bool, str)
    def _on_monitoring_status_update(self, is_running, message):
        """Aggiorna stato monitoraggio"""
        if is_running:
            self.monitor_label.setText(f"Monitoraggio: ▶ {message}")
            self.start_monitor_btn.setEnabled(False)
            self.pause_monitor_btn.setEnabled(True)
            self.stop_monitor_btn.setEnabled(True)
        else:
            self.monitor_label.setText(f"Monitoraggio: ⏸ {message}")
            self.start_monitor_btn.setEnabled(True)
            self.pause_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(False)
    
    def _update_ui(self):
        """Aggiornamento periodico UI"""
        try:
            # Aggiorna stato
            if self.engine.state.last_check:
                self.last_check_label.setText(
                    f"Ultimo controllo: {self.engine.state.last_check.strftime('%H:%M:%S')}"
                )
            
            if self.engine.state.next_check:
                self.next_check_label.setText(
                    f"Prossimo controllo: {self.engine.state.next_check.strftime('%H:%M:%S')}"
                )
            
            # Aggiorna widget attivo
            current_widget = self.tab_widget.currentWidget()
            if hasattr(current_widget, 'refresh'):
                asyncio.ensure_future(current_widget.refresh())
                
        except Exception as e:
            logger.error(f"Errore aggiornamento UI: {e}")
    
    def _start_monitoring(self):
        """Avvia monitoraggio"""
        asyncio.ensure_future(self.engine.start_monitoring())
        self.update_monitoring_status_signal.emit(True, "Attivo")
    
    def _pause_monitoring(self):
        """Pausa monitoraggio"""
        asyncio.ensure_future(self.engine.pause_monitoring())
        self.update_monitoring_status_signal.emit(True, "In pausa")
    
    def _stop_monitoring(self):
        """Ferma monitoraggio"""
        asyncio.ensure_future(self.engine.stop_monitoring())
        self.update_monitoring_status_signal.emit(False, "Fermato")
    
    def _force_check(self):
        """Forza un controllo immediato"""
        self.update_status_signal.emit("🔄", "Esecuzione controllo...")
        asyncio.ensure_future(self.engine.run_full_check())
    
    def _open_settings(self):
        """Apre dialog impostazioni"""
        dialog = SettingsDialog(self.container, self)
        if dialog.exec():
            # Applica modifiche
            self._apply_theme(settings.theme)
            self.update_status_signal.emit("✅", "Impostazioni aggiornate")
    
    def _export_data(self):
        """Esporta dati"""
        QMessageBox.information(
            self,
            "Esporta Dati",
            "Funzionalità di esportazione in sviluppo..."
        )
    
    def _show_about(self):
        """Mostra dialog informazioni"""
        QMessageBox.about(
            self,
            "AI Trading Copilot",
            f"""
            <h2>AI Trading Copilot v{settings.app_version}</h2>
            <p>Assistente intelligente per trading</p>
            <p>© 2024 AI Trading Copilot</p>
            """
        )
    
    def _apply_theme(self, theme: str):
        """Applica tema chiaro/scuro"""
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #444;
                    background-color: #2d2d2d;
                }
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    padding: 8px 16px;
                }
                QTabBar::tab:selected {
                    background-color: #505050;
                }
                QStatusBar {
                    background-color: #007acc;
                    color: white;
                }
                QToolBar {
                    background-color: #2d2d2d;
                    border-bottom: 1px solid #444;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QTabWidget::pane {
                    border: 1px solid #ccc;
                    background-color: white;
                }
                QTabBar::tab {
                    background-color: #e8e8e8;
                    padding: 8px 16px;
                }
                QTabBar::tab:selected {
                    background-color: white;
                }
                QStatusBar {
                    background-color: #0078d7;
                    color: white;
                }
                QToolBar {
                    background-color: #f0f0f0;
                    border-bottom: 1px solid #ccc;
                }
            """)
    
    def closeEvent(self, event):
        """Gestisce chiusura finestra"""
        reply = QMessageBox.question(
            self,
            "Conferma Uscita",
            "Sei sicuro di voler uscire?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.ui_timer.stop()
            event.accept()
        else:
            event.ignore()