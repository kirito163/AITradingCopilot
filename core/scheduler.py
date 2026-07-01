"""
Monitoraggio periodico con APScheduler
"""

import asyncio
from typing import Optional, Callable
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from loguru import logger


class MonitorScheduler:
    """
    Gestisce il monitoraggio periodico del portafoglio
    Supporta avvio/pausa/stop e configurazione intervallo
    """
    
    def __init__(self, engine, scheduler: Optional[AsyncIOScheduler] = None):
        """
        Inizializza lo scheduler
        
        Args:
            engine: Riferimento all'engine principale
            scheduler: Istanza AsyncIOScheduler opzionale
        """
        self.engine = engine
        self.scheduler = scheduler or AsyncIOScheduler()
        self.current_job_id = "portfolio_monitor"
        self._is_running = False
        self._is_paused = False
        
    @property
    def is_running(self) -> bool:
        """Verifica se lo scheduler è in esecuzione"""
        return self._is_running
        
    @property
    def is_paused(self) -> bool:
        """Verifica se lo scheduler è in pausa"""
        return self._is_paused
    
    async def start(self, interval_minutes: int = 5):
        """
        Avvia il monitoraggio periodico
        
        Args:
            interval_minutes: Intervallo in minuti tra i controlli
        """
        if self._is_running:
            await self.stop()
            
        try:
            # Crea trigger con intervallo specificato
            trigger = IntervalTrigger(minutes=interval_minutes)
            
            # Aggiungi job allo scheduler
            self.scheduler.add_job(
                self._execute_check,
                trigger=trigger,
                id=self.current_job_id,
                name="Portfolio Monitor",
                replace_existing=True,
                max_instances=1  # Evita esecuzioni sovrapposte
            )
            
            # Avvia scheduler se non già attivo
            if not self.scheduler.running:
                self.scheduler.start()
            
            self._is_running = True
            self._is_paused = False
            
            next_run = self._get_next_run_time()
            logger.info(
                f"Monitoraggio avviato: ogni {interval_minutes} minuti. "
                f"Prossimo controllo: {next_run}"
            )
            
        except Exception as e:
            logger.error(f"Errore avvio scheduler: {e}")
            raise
    
    async def pause(self):
        """Mette in pausa il monitoraggio"""
        if not self._is_running:
            logger.warning("Scheduler non in esecuzione")
            return
            
        try:
            self.scheduler.pause_job(self.current_job_id)
            self._is_paused = True
            logger.info("Monitoraggio in pausa")
            
        except JobLookupError:
            logger.error(f"Job {self.current_job_id} non trovato")
        except Exception as e:
            logger.error(f"Errore pausa scheduler: {e}")
    
    async def resume(self):
        """Riprende il monitoraggio"""
        if not self._is_running or not self._is_paused:
            logger.warning("Scheduler non in pausa")
            return
            
        try:
            self.scheduler.resume_job(self.current_job_id)
            self._is_paused = False
            
            next_run = self._get_next_run_time()
            logger.info(f"Monitoraggio ripreso. Prossimo controllo: {next_run}")
            
        except JobLookupError:
            logger.error(f"Job {self.current_job_id} non trovato")
        except Exception as e:
            logger.error(f"Errore ripresa scheduler: {e}")
    
    async def stop(self):
        """Ferma completamente il monitoraggio"""
        try:
            # Rimuovi job
            if self.current_job_id in self.scheduler:
                self.scheduler.remove_job(self.current_job_id)
            
            # Ferma scheduler se in esecuzione
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            
            self._is_running = False
            self._is_paused = False
            logger.info("Monitoraggio fermato")
            
        except Exception as e:
            logger.error(f"Errore stop scheduler: {e}")
    
    async def update_interval(self, new_interval_minutes: int):
        """
        Aggiorna l'intervallo di monitoraggio
        
        Args:
            new_interval_minutes: Nuovo intervallo in minuti
        """
        if not self._is_running:
            logger.warning("Scheduler non in esecuzione, impossibile aggiornare")
            return
            
        was_paused = self._is_paused
        
        # Riavvia con nuovo intervallo
        await self.stop()
        await self.start(new_interval_minutes)
        
        if was_paused:
            await self.pause()
            
        logger.info(f"Intervallo aggiornato a {new_interval_minutes} minuti")
    
    async def _execute_check(self):
        """Esegue il controllo programmato"""
        logger.debug("Esecuzione controllo programmato...")
        
        try:
            start_time = datetime.now()
            
            # Esegui controllo completo
            await self.engine.run_full_check()
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Controllo completato in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Errore durante controllo programmato: {e}")
    
    def _get_next_run_time(self) -> Optional[datetime]:
        """Ottiene il prossimo orario di esecuzione"""
        try:
            job = self.scheduler.get_job(self.current_job_id)
            if job:
                return job.next_run_time
        except:
            pass
        return None
    
    def get_status(self) -> dict:
        """Restituisce lo stato corrente dello scheduler"""
        return {
            "is_running": self._is_running,
            "is_paused": self._is_paused,
            "next_run": self._get_next_run_time(),
            "job_exists": self.current_job_id in self.scheduler
        }