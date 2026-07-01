"""
Notification Manager - Gestione notifiche
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from loguru import logger

from config.settings import settings
from database.models import Notification


class NotificationManager:
    """Gestisce invio e storico notifiche"""
    
    def __init__(self, settings, tts_provider=None):
        """
        Inizializza notification manager
        
        Args:
            settings: Settings applicazione
            tts_provider: Provider TTS opzionale
        """
        self.settings = settings
        self.tts_provider = tts_provider
        self.notifications: List[Dict] = []
        
        logger.info("NotificationManager inizializzato")
    
    async def send_notification(self, title: str, message: str,
                               notification_type: str = "info",
                               urgent: bool = False,
                               related_asset: str = None) -> bool:
        """
        Invia notifica su tutti i canali configurati
        
        Args:
            title: Titolo notifica
            message: Messaggio
            notification_type: Tipo notifica
            urgent: Se urgente
            related_asset: Asset correlato
            
        Returns:
            True se inviata con successo
        """
        try:
            notification_data = {
                "title": title,
                "message": message,
                "type": notification_type,
                "urgent": urgent,
                "related_asset": related_asset,
                "timestamp": datetime.now(),
                "acknowledged": False
            }
            
            # Salva in memoria
            self.notifications.insert(0, notification_data)
            
            # Tronca se troppe
            if len(self.notifications) > 1000:
                self.notifications = self.notifications[:1000]
            
            # Popup desktop
            if self.settings.popup_enabled:
                await self._send_desktop_notification(title, message)
            
            # Suono
            if self.settings.sound_enabled:
                await self._play_notification_sound()
            
            # Sintesi vocale
            if self.settings.voice_notifications and self.tts_provider:
                await self._speak_notification(message)
            
            # Salva in database (da implementare con connessione)
            
            logger.info(f"Notifica inviata: [{notification_type}] {title}")
            return True
            
        except Exception as e:
            logger.error(f"Errore invio notifica: {e}")
            return False
    
    async def _send_desktop_notification(self, title: str, message: str):
        """Invia notifica desktop"""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="AI Trading Copilot",
                timeout=5
            )
        except ImportError:
            logger.warning("plyer non installato, notifiche desktop disabilitate")
        except Exception as e:
            logger.error(f"Errore notifica desktop: {e}")
    
    async def _play_notification_sound(self):
        """Riproduce suono notifica"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except ImportError:
            logger.debug("winsound non disponibile (non Windows)")
        except Exception as e:
            logger.error(f"Errore riproduzione suono: {e}")
    
    async def _speak_notification(self, message: str):
        """Notifica vocale"""
        try:
            if self.tts_provider:
                audio = await self.tts_provider.speak(message)
                # Riproduzione audio implementata nella UI
        except Exception as e:
            logger.error(f"Errore sintesi vocale: {e}")
    
    def get_recent_notifications(self, limit: int = 50) -> List[Dict]:
        """Ottieni notifiche recenti"""
        return self.notifications[:limit]
    
    def mark_as_read(self, notification_id: int):
        """Segna notifica come letta"""
        for notification in self.notifications:
            if notification.get("id") == notification_id:
                notification["acknowledged"] = True
                notification["acknowledged_at"] = datetime.now()
                break
    
    def clear_all(self):
        """Pulisci tutte le notifiche"""
        self.notifications.clear()
        logger.info("Tutte le notifiche pulite")
    
    def get_unread_count(self) -> int:
        """Conta notifiche non lette"""
        return sum(1 for n in self.notifications if not n.get("acknowledged", False))