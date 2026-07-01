"""
Widget Dashboard - Visualizzazione principali KPI e metriche
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor, QPalette
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

from loguru import logger


class MetricCard(QFrame):
    """Card per visualizzare una metrica"""
    
    def __init__(self, title: str, value: str = "--", 
                 subtitle: str = "", color: str = "#333"):
        super().__init__()
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame:hover {{
                border-color: #0078d7;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Titolo
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11px; color: #666; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Valore
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        layout.addWidget(self.value_label)
        
        # Sottotitolo
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.subtitle_label)
        
        self.setLayout(layout)
    
    def update_value(self, value: str, subtitle: str = "", color: str = None):
        """Aggiorna il valore della card"""
        self.value_label.setText(str(value))
        if subtitle:
            self.subtitle_label.setText(subtitle)
        if color:
            self.value_label.setStyleSheet(
                f"font-size: 24px; font-weight: bold; color: {color};"
            )


class DashboardWidget(QWidget):
    """Widget principale della dashboard"""
    
    update_signal = Signal(dict)
    
    def __init__(self, engine, container):
        super().__init__()
        self.engine = engine
        self.container = container
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Configura l'interfaccia della dashboard"""
        main_layout = QVBoxLayout()
        
        # Titolo
        title = QLabel("Dashboard Portfolio")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Griglia metriche principali
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        
        # Valore totale portafoglio
        self.total_value_card = MetricCard(
            "Valore Totale Portafoglio",
            "€ 0.00",
            "In attesa dati..."
        )
        metrics_grid.addWidget(self.total_value_card, 0, 0)
        
        # Profitto/Perdita totale
        self.total_pnl_card = MetricCard(
            "Profitto/Perdita Totale",
            "€ 0.00 (0.00%)",
            "Dall'inizio"
        )
        metrics_grid.addWidget(self.total_pnl_card, 0, 1)
        
        # Profitto giornaliero
        self.daily_pnl_card = MetricCard(
            "P&L Giornaliero",
            "€ 0.00 (0.00%)",
            "Oggi"
        )
        metrics_grid.addWidget(self.daily_pnl_card, 0, 2)
        
        # ROI
        self.roi_card = MetricCard(
            "ROI",
            "0.00%",
            "Return on Investment"
        )
        metrics_grid.addWidget(self.roi_card, 1, 0)
        
        # Drawdown
        self.drawdown_card = MetricCard(
            "Drawdown",
            "0.00%",
            "Massimo storico"
        )
        metrics_grid.addWidget(self.drawdown_card, 1, 1)
        
        # Posizioni aperte
        self.open_positions_card = MetricCard(
            "Posizioni Aperte",
            "0",
            "Attive"
        )
        metrics_grid.addWidget(self.open_positions_card, 1, 2)
        
        # Win Rate
        self.win_rate_card = MetricCard(
            "Win Rate",
            "0%",
            "Trade vincenti"
        )
        metrics_grid.addWidget(self.win_rate_card, 2, 0)
        
        # Sharpe Ratio
        self.sharpe_card = MetricCard(
            "Sharpe Ratio",
            "0.00",
            "Rendimento/Rischio"
        )
        metrics_grid.addWidget(self.sharpe_card, 2, 1)
        
        # Volatilità
        self.volatility_card = MetricCard(
            "Volatilità",
            "0.00%",
            "30 giorni"
        )
        metrics_grid.addWidget(self.volatility_card, 2, 2)
        
        main_layout.addLayout(metrics_grid)
        
        # Stato AI e monitoraggio
        status_layout = QHBoxLayout()
        
        # Stato AI
        ai_frame = QFrame()
        ai_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        ai_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        ai_layout = QVBoxLayout()
        
        ai_title = QLabel("🤖 Stato AI")
        ai_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        ai_layout.addWidget(ai_title)
        
        self.ai_status_label = QLabel("Provider: --\nModello: --")
        self.ai_status_label.setStyleSheet("font-size: 11px; color: #666;")
        ai_layout.addWidget(self.ai_status_label)
        
        ai_frame.setLayout(ai_layout)
        status_layout.addWidget(ai_frame)
        
        # Stato monitoraggio
        monitor_frame = QFrame()
        monitor_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        monitor_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        monitor_layout = QVBoxLayout()
        
        monitor_title = QLabel("⏱ Monitoraggio")
        monitor_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        monitor_layout.addWidget(monitor_title)
        
        self.monitor_status_label = QLabel(
            "Stato: In pausa\n"
            "Ultimo controllo: --\n"
            "Prossimo controllo: --\n"
            "Analisi effettuate: 0"
        )
        self.monitor_status_label.setStyleSheet("font-size: 11px; color: #666;")
        monitor_layout.addWidget(self.monitor_status_label)
        
        monitor_frame.setLayout(monitor_layout)
        status_layout.addWidget(monitor_frame)
        
        # Performance recente
        perf_frame = QFrame()
        perf_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        perf_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        perf_layout = QVBoxLayout()
        
        perf_title = QLabel("📈 Performance Recente")
        perf_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        perf_layout.addWidget(perf_title)
        
        self.performance_label = QLabel(
            "Oggi: --\n"
            "Settimana: --\n"
            "Mese: --\n"
            "Anno: --"
        )
        self.performance_label.setStyleSheet("font-size: 11px; color: #666;")
        perf_layout.addWidget(self.performance_label)
        
        perf_frame.setLayout(perf_layout)
        status_layout.addWidget(perf_frame)
        
        main_layout.addLayout(status_layout)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def connect_signals(self):
        """Connetti segnali"""
        self.update_signal.connect(self.on_data_update)
        
        # Timer aggiornamento automatico
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(lambda: asyncio.ensure_future(self.refresh()))
        self.refresh_timer.start(10000)  # 10 secondi
    
    async def refresh(self):
        """Aggiorna i dati della dashboard"""
        try:
            summary = await self.engine.get_portfolio_summary()
            self.update_signal.emit(summary)
        except Exception as e:
            logger.error(f"Errore refresh dashboard: {e}")
    
    @Slot(dict)
    def on_data_update(self, data: Dict[str, Any]):
        """Aggiorna UI con nuovi dati"""
        try:
            # Valore totale
            total_value = data.get("total_value", 0)
            self.total_value_card.update_value(
                f"€ {total_value:,.2f}",
                f"Aggiornato: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # P&L totale
            total_pnl = data.get("total_pnl_eur", 0)
            total_pnl_pct = data.get("total_pnl_pct", 0)
            pnl_color = "#28a745" if total_pnl >= 0 else "#dc3545"
            self.total_pnl_card.update_value(
                f"€ {total_pnl:+,.2f}",
                f"{total_pnl_pct:+.2f}% totale",
                pnl_color
            )
            
            # P&L giornaliero
            daily_pnl = data.get("daily_pnl_eur", 0)
            daily_pnl_pct = data.get("daily_pnl_pct", 0)
            daily_color = "#28a745" if daily_pnl >= 0 else "#dc3545"
            self.daily_pnl_card.update_value(
                f"€ {daily_pnl:+,.2f}",
                f"{daily_pnl_pct:+.2f}% oggi",
                daily_color
            )
            
            # ROI
            roi = data.get("roi", 0)
            self.roi_card.update_value(
                f"{roi:+.2f}%",
                f"Return on Investment",
                "#28a745" if roi >= 0 else "#dc3545"
            )
            
            # Drawdown
            drawdown = data.get("drawdown", 0)
            self.drawdown_card.update_value(
                f"{drawdown:.2f}%",
                "Massimo drawdown",
                "#dc3545"
            )
            
            # Posizioni aperte
            open_pos = data.get("open_positions", 0)
            self.open_positions_card.update_value(
                str(open_pos),
                "Attive"
            )
            
            # Win Rate
            win_rate = data.get("win_rate", 0)
            self.win_rate_card.update_value(
                f"{win_rate:.1f}%",
                f"{data.get('winning_trades', 0)}/{data.get('total_trades', 0)} trades"
            )
            
            # Sharpe Ratio
            sharpe = data.get("sharpe_ratio", 0)
            self.sharpe_card.update_value(
                f"{sharpe:.2f}",
                "Rendimento corretto per rischio"
            )
            
            # Volatilità
            volatility = data.get("volatility", 0)
            self.volatility_card.update_value(
                f"{volatility:.2f}%",
                "Deviazione standard 30gg"
            )
            
            # Aggiorna stato AI
            self.ai_status_label.setText(
                f"Provider: {self.container.settings.ai_provider}\n"
                f"Modello: {self.container.settings.ai_model}\n"
                f"Temperatura: {self.container.settings.ai_temperature}"
            )
            
            # Aggiorna stato monitoraggio
            engine_state = self.engine.state
            last_check = engine_state.last_check.strftime('%H:%M:%S') if engine_state.last_check else "--"
            next_check = engine_state.next_check.strftime('%H:%M:%S') if engine_state.next_check else "--"
            
            self.monitor_status_label.setText(
                f"Stato: {'🟢 Attivo' if engine_state.is_monitoring else '⏸ In pausa'}\n"
                f"Ultimo controllo: {last_check}\n"
                f"Prossimo controllo: {next_check}\n"
                f"Analisi effettuate: {engine_state.total_analyses}"
            )
            
            # Performance recente
            perf_week = data.get("performance_week", 0)
            perf_month = data.get("performance_month", 0)
            perf_year = data.get("performance_year", 0)
            
            self.performance_label.setText(
                f"Oggi: {daily_pnl_pct:+.2f}%\n"
                f"Settimana: {perf_week:+.2f}%\n"
                f"Mese: {perf_month:+.2f}%\n"
                f"Anno: {perf_year:+.2f}%"
            )
            
        except Exception as e:
            logger.error(f"Errore aggiornamento dashboard UI: {e}")