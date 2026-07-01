"""
Logger per notifiche (salvataggio su database e storico)
"""

from typing import List, Dict, Optional
from datetime import datetime
from collections import deque
from loguru import logger


class NotificationLogger:
    """Gestisce lo storico delle notifiche in memoria e su database"""

    MAX_HISTORY = 500  # Numero massimo notifiche in memoria

    def __init__(self, database_manager=None):
        self.db = database_manager
        self._notifications = deque(maxlen=self.MAX_HISTORY)
        self._unread_count = 0

    async def log(self, title: str, message: str, notification_type: str = "info",
                  urgent: bool = False, related_asset: Optional[str] = None):
        """
        Registra una notifica nello storico

        Args:
            title: Titolo
            message: Messaggio
            notification_type: Tipo (info, alert, trade, ai_suggestion, performance)
            urgent: Flag urgenza
            related_asset: Asset associato
        """
        notification = {
            "id": len(self._notifications) + 1,  # ID temporaneo
            "title": title,
            "message": message,
            "type": notification_type,
            "urgent": urgent,
            "related_asset": related_asset,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False
        }
        self._notifications.appendleft(notification)
        self._unread_count += 1

        # Salva su database se disponibile
        if self.db:
            try:
                from database.models import Notification
                db_notification = Notification(
                    type=notification_type,
                    title=title,
                    message=message,
                    urgent=urgent,
                    related_asset=related_asset,
                    acknowledged=False
                )
                await self.db.add(db_notification)
                await self.db.commit()
                notification["db_id"] = db_notification.id
            except Exception as e:
                logger.error(f"Errore salvataggio notifica su DB: {e}")

        logger.debug(f"Notifica registrata: [{notification_type}] {title}")

    async def mark_read(self, notification_id: int):
        """Segna una notifica come letta"""
        for n in self._notifications:
            if n.get("id") == notification_id or n.get("db_id") == notification_id:
                if not n["acknowledged"]:
                    n["acknowledged"] = True
                    self._unread_count = max(0, self._unread_count - 1)
                break

    async def mark_all_read(self):
        """Segna tutte come lette"""
        for n in self._notifications:
            n["acknowledged"] = True
        self._unread_count = 0

    def get_all(self, include_acknowledged: bool = True) -> List[Dict]:
        """Restituisce notifiche in memoria"""
        if include_acknowledged:
            return list(self._notifications)
        return [n for n in self._notifications if not n["acknowledged"]]

    def get_unread_count(self) -> int:
        return self._unread_count

    async def clear(self):
        """Pulisce lo storico in memoria (non cancella dal DB)"""
        self._notifications.clear()
        self._unread_count = 0