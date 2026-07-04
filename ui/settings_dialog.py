"""
Dialog Impostazioni - Configurazione completa applicazione
"""

import asyncio

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QLineEdit, QPushButton,
    QCheckBox, QGroupBox, QDialogButtonBox,
    QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any

from loguru import logger
from config.settings import settings

_STT_ENGINE_FOR_MODEL = {
    "whisper-base-it": "whisper_local",
    "whisper-small-it": "whisper_local",
    "vosk-model-it-0.22": "vosk",
}
_TTS_ENGINE_FOR_MODEL = {
    "piper-it-voice1": "piper",
}


class SettingsDialog(QDialog):
    """Dialog configurazione impostazioni"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.settings = settings
        
        self.setWindowTitle("⚙ Impostazioni")
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Configura interfaccia dialog"""
        layout = QVBoxLayout()
        
        # Tab widget per categorie
        self.tab_widget = QTabWidget()
        
        # Tab AI
        self.tab_widget.addTab(self._create_ai_tab(), "🤖 AI")
        
        # Tab Broker
        self.tab_widget.addTab(self._create_broker_tab(), "🏦 Broker")
        
        # Tab Market Data
        self.tab_widget.addTab(self._create_market_tab(), "📊 Mercati")
        
        # Tab Voice
        self.tab_widget.addTab(self._create_voice_tab(), "🎤 Voce")
        
        # Tab Monitoraggio
        self.tab_widget.addTab(self._create_monitoring_tab(), "⏱ Monitoraggio")
        
        # Tab Notifiche
        self.tab_widget.addTab(self._create_notifications_tab(), "🔔 Notifiche")
        
        # Tab UI
        self.tab_widget.addTab(self._create_ui_tab(), "🎨 Interfaccia")
        
        layout.addWidget(self.tab_widget)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _create_ai_tab(self) -> QWidget:
        """Crea tab configurazione AI"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Provider AI
        provider_group = QGroupBox("Provider AI")
        provider_layout = QFormLayout()
        
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems([
            "openai", "anthropic", "gemini", "openrouter", "ollama"
        ])
        self.ai_provider_combo.currentTextChanged.connect(self._on_ai_provider_changed)
        provider_layout.addRow("Provider:", self.ai_provider_combo)
        
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.setEditable(True)
        provider_layout.addRow("Modello:", self.ai_model_combo)
        
        # API Keys
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("OpenAI API Key:", self.openai_key_input)
        
        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("Anthropic API Key:", self.anthropic_key_input)
        
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("Gemini API Key:", self.gemini_key_input)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Parametri AI
        params_group = QGroupBox("Parametri")
        params_layout = QFormLayout()
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        params_layout.addRow("Temperature:", self.temperature_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 128000)
        self.max_tokens_spin.setValue(1500)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" sec")
        params_layout.addRow("Timeout:", self.timeout_spin)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Prompt Template
        prompt_group = QGroupBox("Prompt Template")
        prompt_layout = QVBoxLayout()
        
        self.prompt_profile_combo = QComboBox()
        self.prompt_profile_combo.addItems([
            "Swing Trading Expert",
            "Day Trading Expert",
            "Crypto Expert",
            "ETF Expert",
            "Value Investing Expert",
            "Personalizzato"
        ])
        prompt_layout.addWidget(self.prompt_profile_combo)
        
        self.custom_prompt_edit = QLineEdit()
        self.custom_prompt_edit.setPlaceholderText(
            "Prompt personalizzato..."
        )
        self.custom_prompt_edit.setEnabled(False)
        prompt_layout.addWidget(self.custom_prompt_edit)
        
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_broker_tab(self) -> QWidget:
        """Crea tab configurazione broker"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Provider broker
        self.broker_combo = QComboBox()
        self.broker_combo.addItems([
            "paper_trading", "interactive_brokers", "binance", 
            "coinbase", "kraken"
        ])
        layout.addWidget(QLabel("Broker predefinito:"))
        layout.addWidget(self.broker_combo)
        
        # Configurazioni specifiche
        ib_group = QGroupBox("Interactive Brokers")
        ib_layout = QFormLayout()
        self.ib_host = QLineEdit("127.0.0.1")
        self.ib_port = QSpinBox()
        self.ib_port.setRange(1, 65535)
        self.ib_port.setValue(7497)
        ib_layout.addRow("Host:", self.ib_host)
        ib_layout.addRow("Port:", self.ib_port)
        ib_group.setLayout(ib_layout)
        layout.addWidget(ib_group)
        
        # API Keys per exchange crypto
        crypto_group = QGroupBox("Exchange Crypto")
        crypto_layout = QFormLayout()
        
        self.binance_key = QLineEdit()
        self.binance_key.setEchoMode(QLineEdit.Password)
        crypto_layout.addRow("Binance API Key:", self.binance_key)
        
        self.binance_secret = QLineEdit()
        self.binance_secret.setEchoMode(QLineEdit.Password)
        crypto_layout.addRow("Binance Secret:", self.binance_secret)
        
        crypto_group.setLayout(crypto_layout)
        layout.addWidget(crypto_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_market_tab(self) -> QWidget:
        """Crea tab configurazione market data"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.market_provider_combo = QComboBox()
        self.market_provider_combo.addItems([
            "yahoo_finance", "alpha_vantage", "finnhub", "polygon", "twelve_data"
        ])
        layout.addWidget(QLabel("Provider Market Data:"))
        layout.addWidget(self.market_provider_combo)
        
        # API Keys
        keys_group = QGroupBox("API Keys")
        keys_layout = QFormLayout()
        
        self.alpha_vantage_key = QLineEdit()
        self.alpha_vantage_key.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("Alpha Vantage:", self.alpha_vantage_key)
        
        self.finnhub_key = QLineEdit()
        self.finnhub_key.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("Finnhub:", self.finnhub_key)
        
        self.polygon_key = QLineEdit()
        self.polygon_key.setEchoMode(QLineEdit.Password)
        keys_layout.addRow("Polygon:", self.polygon_key)
        
        keys_group.setLayout(keys_layout)
        layout.addWidget(keys_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_voice_tab(self) -> QWidget:
        """Crea tab configurazione voce"""
        widget = QWidget()
        layout = QVBoxLayout()

        # STT
        stt_group = QGroupBox("🎙 Speech to Text (Locale)")
        stt_layout = QVBoxLayout()

        stt_desc = QLabel("Riconoscimento vocale per la trascrizione dei comandi vocali dell'utente.")
        stt_desc.setWordWrap(True)
        stt_desc.setStyleSheet("color: gray; font-size: 11px;")
        stt_layout.addWidget(stt_desc)

        self.stt_enabled_cb = QCheckBox("Abilita STT")
        self.stt_enabled_cb.setChecked(True)
        self.stt_enabled_cb.stateChanged.connect(self._on_stt_enabled_changed)
        stt_layout.addWidget(self.stt_enabled_cb)

        stt_layout.addWidget(QLabel("Modello STT"))
        self.stt_model_combo = QComboBox()
        self.stt_model_combo.addItems([
            "whisper-base-it",
            "whisper-small-it",
            "vosk-model-it-0.22"
        ])
        self.stt_model_combo.currentTextChanged.connect(self._update_stt_status)
        stt_layout.addWidget(self.stt_model_combo)

        self.stt_status_label = QLabel("Nessun modello installato")
        self.stt_status_label.setStyleSheet("color: gray; font-size: 11px;")
        stt_layout.addWidget(self.stt_status_label)

        self.stt_download_btn = QPushButton("⬇ Scarica modello STT")
        self.stt_download_btn.clicked.connect(self._download_stt_model)
        stt_layout.addWidget(self.stt_download_btn)

        stt_group.setLayout(stt_layout)
        layout.addWidget(stt_group)

        # TTS
        tts_group = QGroupBox("🔊 Text to Speech (Locale)")
        tts_layout = QVBoxLayout()

        tts_desc = QLabel("Sintesi vocale per la risposta dell'assistente.")
        tts_desc.setWordWrap(True)
        tts_desc.setStyleSheet("color: gray; font-size: 11px;")
        tts_layout.addWidget(tts_desc)

        self.tts_enabled_cb = QCheckBox("Abilita TTS")
        self.tts_enabled_cb.setChecked(True)
        self.tts_enabled_cb.stateChanged.connect(self._on_tts_enabled_changed)
        tts_layout.addWidget(self.tts_enabled_cb)

        tts_layout.addWidget(QLabel("Modello TTS"))
        self.tts_model_combo = QComboBox()
        self.tts_model_combo.addItems([
            "piper-it-voice1"
        ])
        self.tts_model_combo.currentTextChanged.connect(self._update_tts_status)
        tts_layout.addWidget(self.tts_model_combo)

        self.tts_status_label = QLabel("Nessun modello installato")
        self.tts_status_label.setStyleSheet("color: gray; font-size: 11px;")
        tts_layout.addWidget(self.tts_status_label)

        self.tts_download_btn = QPushButton("⬇ Scarica modello TTS")
        self.tts_download_btn.clicked.connect(self._download_tts_model)
        tts_layout.addWidget(self.tts_download_btn)

        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

        layout.addStretch()
        widget.setLayout(layout)

        # Stato iniziale coerente con checkbox e combo già popolate
        self._on_stt_enabled_changed(self.stt_enabled_cb.checkState())
        self._on_tts_enabled_changed(self.tts_enabled_cb.checkState())
        self._update_stt_status(self.stt_model_combo.currentText())
        self._update_tts_status(self.tts_model_combo.currentText())

        return widget

    def _on_stt_enabled_changed(self, state):
        enabled = bool(state)
        self.stt_model_combo.setEnabled(enabled)
        self.stt_download_btn.setEnabled(enabled)

    def _on_tts_enabled_changed(self, state):
        enabled = bool(state)
        self.tts_model_combo.setEnabled(enabled)
        self.tts_download_btn.setEnabled(enabled)
    
    def _model_info(self, model_name: str, provider_type: str):
        """Recupera le info aggiornate di un modello dal catalogo"""
        for m in self.container.voice_model_manager.get_available_models():
            if m.name == model_name and m.provider == provider_type:
                return m
        return None

    def _update_stt_status(self, model_name: str):
        if not model_name:
            return
        info = self._model_info(model_name, "stt")
        if info and info.installed:
            self.stt_status_label.setText(f"✅ Modello installato ({info.size_mb:.0f} MB)")
            self.stt_download_btn.setText("⬇ Ri-scarica modello STT")
        elif info:
            self.stt_status_label.setText(f"Non installato · {info.size_mb:.0f} MB da scaricare")
            self.stt_download_btn.setText("⬇ Scarica modello STT")
        else:
            self.stt_status_label.setText("Nessun modello installato")
 
    def _update_tts_status(self, model_name: str):
        if not model_name:
            return
        info = self._model_info(model_name, "tts")
        if info and info.installed:
            self.tts_status_label.setText(f"✅ Modello installato ({info.size_mb:.0f} MB)")
            self.tts_download_btn.setText("⬇ Ri-scarica modello TTS")
        elif info:
            self.tts_status_label.setText(f"Non installato · {info.size_mb:.0f} MB da scaricare")
            self.tts_download_btn.setText("⬇ Scarica modello TTS")
        else:
            self.tts_status_label.setText("Nessun modello installato")
 
    def _download_stt_model(self):
        model_name = self.stt_model_combo.currentText()
        reply = QMessageBox.question(
            self, "Scarica modello STT",
            f"Scaricare il modello '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
 
        self.stt_download_btn.setEnabled(False)
        self.stt_status_label.setText("Download in corso...")
        self._start_download("stt", model_name)
 
    def _download_tts_model(self):
        model_name = self.tts_model_combo.currentText()
        reply = QMessageBox.question(
            self, "Scarica modello TTS",
            f"Scaricare il modello '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
 
        self.tts_download_btn.setEnabled(False)
        self.tts_status_label.setText("Download in corso...")
        self._start_download("tts", model_name)

    def _start_download(self, kind: str, model_name: str):
        """Avvia il download (bloccante) in un QThread separato per non congelare la UI."""
        from PySide6.QtCore import QThread, Signal, QObject

        class _Worker(QObject):
            finished = Signal(str, str, bool)

            def __init__(self, manager, kind, model_name):
                super().__init__()
                self.manager = manager
                self.kind = kind
                self.model_name = model_name

            def run(self):
                success = self.manager.download_model(self.model_name)
                self.finished.emit(self.kind, self.model_name, success)

        if not hasattr(self, "_download_threads"):
            self._download_threads = []

        thread = QThread(self)
        worker = _Worker(self.container.voice_model_manager, kind, model_name)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_download_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._download_threads.append((thread, worker))
        thread.start()

    def _on_download_finished(self, kind: str, model_name: str, success: bool):
        if kind == "stt":
            self.stt_download_btn.setEnabled(self.stt_enabled_cb.isChecked())
            self._update_stt_status(model_name)
        else:
            self.tts_download_btn.setEnabled(self.tts_enabled_cb.isChecked())
            self._update_tts_status(model_name)

        if success:
            QMessageBox.information(self, "Download completato", f"Modello '{model_name}' scaricato con successo.")
        else:
            QMessageBox.critical(self, "Download fallito", f"Impossibile scaricare il modello '{model_name}'. Controlla i log.")
    
    def _create_monitoring_tab(self) -> QWidget:
        """Crea tab configurazione monitoraggio"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Intervallo monitoraggio
        interval_group = QGroupBox("Intervallo Monitoraggio")
        interval_layout = QFormLayout()
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems([
            "1 minuto", "5 minuti", "10 minuti", "15 minuti",
            "30 minuti", "1 ora", "Personalizzato"
        ])
        interval_layout.addRow("Frequenza:", self.interval_combo)
        
        self.custom_interval = QSpinBox()
        self.custom_interval.setRange(1, 1440)
        self.custom_interval.setValue(5)
        self.custom_interval.setSuffix(" minuti")
        self.custom_interval.setEnabled(False)
        interval_layout.addRow("Minuti:", self.custom_interval)
        
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # Opzioni monitoraggio
        options_group = QGroupBox("Opzioni")
        options_layout = QVBoxLayout()
        
        self.auto_update_cb = QCheckBox("Aggiorna automaticamente prezzi")
        self.auto_update_cb.setChecked(True)
        options_layout.addWidget(self.auto_update_cb)
        
        self.fetch_news_cb = QCheckBox("Recupera news di mercato")
        self.fetch_news_cb.setChecked(True)
        options_layout.addWidget(self.fetch_news_cb)
        
        self.analyze_positions_cb = QCheckBox("Analizza posizioni con AI")
        self.analyze_positions_cb.setChecked(True)
        options_layout.addWidget(self.analyze_positions_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_notifications_tab(self) -> QWidget:
        """Crea tab configurazione notifiche"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Canali notifica
        channels_group = QGroupBox("Canali di Notifica")
        channels_layout = QVBoxLayout()
        
        self.popup_cb = QCheckBox("Popup desktop")
        self.popup_cb.setChecked(True)
        channels_layout.addWidget(self.popup_cb)
        
        self.sound_cb = QCheckBox("Suoni")
        channels_layout.addWidget(self.sound_cb)
        
        self.voice_cb = QCheckBox("Sintesi vocale")
        channels_layout.addWidget(self.voice_cb)
        
        channels_group.setLayout(channels_layout)
        layout.addWidget(channels_group)
        
        # Tipi notifica
        types_group = QGroupBox("Tipi di Notifica")
        types_layout = QVBoxLayout()
        
        self.notify_ai_cb = QCheckBox("Suggerimenti AI")
        self.notify_ai_cb.setChecked(True)
        types_layout.addWidget(self.notify_ai_cb)
        
        self.notify_trade_cb = QCheckBox("Operazioni di trading")
        self.notify_trade_cb.setChecked(True)
        types_layout.addWidget(self.notify_trade_cb)
        
        self.notify_performance_cb = QCheckBox("Performance")
        self.notify_performance_cb.setChecked(True)
        types_layout.addWidget(self.notify_performance_cb)
        
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_ui_tab(self) -> QWidget:
        """Crea tab configurazione interfaccia"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tema
        theme_group = QGroupBox("Tema")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        theme_layout.addRow("Tema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["it", "en", "fr", "de", "es"])
        theme_layout.addRow("Lingua:", self.language_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("Livello Log:", self.log_level_combo)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def load_settings(self):
        """Carica impostazioni correnti"""
        # AI
        self.ai_provider_combo.setCurrentText(self.settings.ai_provider)
        self.ai_model_combo.setCurrentText(self.settings.ai_model)
        self.temperature_spin.setValue(self.settings.ai_temperature)
        self.max_tokens_spin.setValue(self.settings.ai_max_tokens)
        
        # Broker
        self.broker_combo.setCurrentText(self.settings.broker_provider)
        
        # Market
        self.market_provider_combo.setCurrentText(self.settings.market_data_provider)
        
        # Voice
        self.stt_enabled_cb.setChecked(self.settings.stt_enabled)
        self.tts_enabled_cb.setChecked(self.settings.tts_enabled)
        stt_idx = self.stt_model_combo.findText(self.settings.stt_model_name)
        if stt_idx >= 0:
            self.stt_model_combo.setCurrentIndex(stt_idx)
        tts_idx = self.tts_model_combo.findText(self.settings.tts_model_name)
        if tts_idx >= 0:
            self.tts_model_combo.setCurrentIndex(tts_idx)
        # Forza l'aggiornamento degli status label anche se l'indice non cambia
        self._update_stt_status(self.stt_model_combo.currentText())
        self._update_tts_status(self.tts_model_combo.currentText())
        
        # UI
        self.theme_combo.setCurrentText(self.settings.theme)
        self.log_level_combo.setCurrentText(self.settings.log_level)
    
    def apply_settings(self):
        """Applica impostazioni"""
        try:
            # AI
            self.settings.ai_provider = self.ai_provider_combo.currentText()
            self.settings.ai_model = self.ai_model_combo.currentText()
            self.settings.ai_temperature = self.temperature_spin.value()
            self.settings.ai_max_tokens = self.max_tokens_spin.value()
            self.settings.ai_api_key = self.openai_key_input.text() or None
            
            # Broker
            self.settings.broker_provider = self.broker_combo.currentText()
            
            # Market Data
            self.settings.market_data_provider = self.market_provider_combo.currentText()
            
            # Voice
            self.settings.stt_enabled = self.stt_enabled_cb.isChecked()
            self.settings.tts_enabled = self.tts_enabled_cb.isChecked()
            self.settings.stt_model_name = self.stt_model_combo.currentText()
            self.settings.tts_model_name = self.tts_model_combo.currentText()
            self.settings.stt_provider = (
                _STT_ENGINE_FOR_MODEL.get(self.settings.stt_model_name, "disabled")
                if self.settings.stt_enabled else "disabled"
            )
            self.settings.tts_provider = (
                _TTS_ENGINE_FOR_MODEL.get(self.settings.tts_model_name, "disabled")
                if self.settings.tts_enabled else "disabled"
            )
            
            # UI
            self.settings.theme = self.theme_combo.currentText()
            self.settings.log_level = self.log_level_combo.currentText()

            # LANGUAGE
            self.settings.language = self.language_combo.currentText()
            
            # Notifiche
            self.settings.popup_enabled = self.popup_cb.isChecked()
            self.settings.sound_enabled = self.sound_cb.isChecked()
            self.settings.voice_notifications = self.voice_cb.isChecked()
            
            # Monitoraggio
            self.settings.auto_update_prices = self.auto_update_cb.isChecked()
            
            # Salva su file .env
            self._save_to_env()
            
            # Emetti segnale
            self.settings_changed.emit(self.settings.dict())
            
            logger.info("Impostazioni applicate con successo")
            
        except Exception as e:
            logger.error(f"Errore applicazione impostazioni: {e}")
            QMessageBox.critical(self, "Errore", f"Impossibile applicare impostazioni: {e}")
    
    def save_and_close(self):
        """Salva e chiudi"""
        self.apply_settings()
        self.accept()
    
    def _save_to_env(self):
        """Salva impostazioni su file .env"""
        try:
            with open(".env", "w") as f:
                for key, value in self.settings.dict().items():
                    if value is not None:
                        f.write(f"AI_TRADING_{key.upper()}={value}\n")
        except Exception as e:
            logger.error(f"Errore salvataggio .env: {e}")
    
    def _on_ai_provider_changed(self, provider: str):
        """Aggiorna modelli disponibili in base al provider"""
        models = {
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "gemini": ["gemini-pro", "gemini-ultra"],
            "openrouter": ["openai/gpt-4", "anthropic/claude-3"],
            "ollama": ["llama3", "mistral", "codellama"]
        }
        
        self.ai_model_combo.clear()
        self.ai_model_combo.addItems(models.get(provider, []))