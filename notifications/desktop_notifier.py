"""
Notifiche desktop native multipiattaforma
"""

import asyncio
from typing import Optional
from loguru import logger


class DesktopNotifier:
    """Gestisce notifiche popup sul desktop"""

    def __init__(self, app_name: str = "AI Trading Copilot"):
        self.app_name = app_name
        self._enabled = True
        self._check_availability()

    def _check_availability(self):
        """Verifica disponibilità librerie di notifica"""
        try:
            import plyer
            self._backend = "plyer"
            logger.info("DesktopNotifier: usando plyer")
        except ImportError:
            try:
                # Windows
                from win10toast import ToastNotifier
                self._backend = "win10toast"
                self._toaster = ToastNotifier()
                logger.info("DesktopNotifier: usando win10toast")
            except ImportError:
                logger.warning("Nessuna libreria di notifiche desktop trovata. Le notifiche popup sono disabilitate.")
                self._enabled = False

    async def send(self, title: str, message: str, duration: int = 5, urgent: bool = False) -> bool:
        """
        Invia una notifica desktop

        Args:
            title: Titolo della notifica
            message: Corpo del messaggio
            duration: Durata in secondi
            urgent: Se True, icona critica

        Returns:
            True se inviata con successo
        """
        if not self._enabled:
            return False

        try:
            if self._backend == "plyer":
                from plyer import notification
                # plyer è bloccante, esegui in thread
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: notification.notify(
                        title=title,
                        message=message,
                        app_name=self.app_name,
                        timeout=duration,
                        toast_icon="warning" if urgent else "info"
                    )
                )
                return True
            elif self._backend == "win10toast":
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._toaster.show_toast(
                        title,
                        message,
                        duration=duration,
                        threaded=True
                    )
                )
                return True
        except Exception as e:
            logger.error(f"Errore invio notifica desktop: {e}")
            return False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False