"""
AI Trading Copilot - Entry Point
Application desktop per assistenza trading con AI
"""

import sys
import asyncio
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from loguru import logger

from config.settings import settings
from config.logging_config import setup_logging
from core.dependency_injection import Container
from core.engine import CopilotEngine
from ui.main_window import MainWindow


async def main():
    """Funzione principale asincrona"""
    
    # Setup logging
    setup_logging(settings.log_level)
    logger.info("Avvio AI Trading Copilot...")
    
    # Crea applicazione Qt
    app = QApplication(sys.argv)
    app.setApplicationName("AI Trading Copilot")
    app.setOrganizationName("AITradingCopilot")
    
    # Imposta stile globale
    app.setStyle("Fusion")
    
    # Crea container dependency injection
    container = Container()
    
    try:
        # Inizializza database
        await container.init_database()
        logger.info("Database inizializzato")
        
        # Inizializza engine
        engine = CopilotEngine(container)
        await engine.initialize()
        logger.info("Engine inizializzato")
        
        # Crea e mostra finestra principale
        window = MainWindow(engine, container)
        window.show()
        
        # Timer per operazioni asincrone Qt
        timer = QTimer()
        timer.timeout.connect(lambda: asyncio.ensure_future(engine.process_async_tasks()))
        timer.start(100)  # 100ms interval
        
        # Avvia applicazione
        exit_code = app.exec()
        
        # Cleanup
        await engine.shutdown()
        logger.info("Applicazione terminata")
        
    except Exception as e:
        logger.error(f"Errore critico: {e}")
        return 1
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interruzione utente")
        sys.exit(0)