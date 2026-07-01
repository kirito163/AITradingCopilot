"""
Configurazione logging con loguru
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Configura il sistema di logging
    
    Args:
        level: Livello di logging
        log_file: Percorso file di log
    """
    # Rimuovi handler predefinito
    logger.remove()
    
    # Formato personalizzato
    format_console = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    format_file = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # Console handler
    logger.add(
        sys.stderr,
        format=format_console,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File handler
    if log_file is None:
        log_file = "logs/trading_copilot.log"
    
    # Crea directory logs se non esiste
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format=format_file,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True  # Thread-safe
    )
    
    logger.info(f"Logging configurato con livello: {level}")
    
    # Log delle eccezioni non catturate
    import traceback
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = exception_handler