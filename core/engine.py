"""
Orchestratore principale dell'applicazione
Coordina tutti i componenti e gestisce il flusso principale
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from loguru import logger

from core.dependency_injection import Container
from core.scheduler import MonitorScheduler
from database.models import PortfolioHolding, AnalysisHistory
from ai.prompt_manager import PromptManager
from ai.base import AIRequest


@dataclass
class EngineState:
    """Stato dell'engine"""
    is_running: bool = False
    is_monitoring: bool = False
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
    total_analyses: int = 0
    errors_count: int = 0


class CopilotEngine:
    """Engine principale del Trading Copilot"""
    
    def __init__(self, container: Container):
        """
        Inizializza l'engine con dependency injection
        
        Args:
            container: Container DI con tutti i servizi
        """
        self.container = container
        self.state = EngineState()
        self.scheduler = MonitorScheduler(self)
        self.async_tasks: List[asyncio.Task] = []
        
        logger.info("CopilotEngine creato")
    
    async def initialize(self) -> bool:
        """
        Inizializza tutti i componenti
        
        Returns:
            True se inizializzazione completata con successo
        """
        try:
            logger.info("Inizializzazione engine...")
            
            # Inizializza portfolio
            await self.container.portfolio_manager.initialize()
            
            # Carica configurazioni da database
            await self._load_settings()
            
            # Avvia scheduler se monitoring era attivo
            if self.container.settings.monitoring_enabled:
                await self.scheduler.start(
                    self.container.settings.monitoring_interval_minutes
                )
                self.state.is_monitoring = True
            
            self.state.is_running = True
            logger.info("Engine inizializzato con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore inizializzazione engine: {e}")
            return False
    
    async def shutdown(self):
        """Spegnimento controllato dell'engine"""
        logger.info("Spegnimento engine...")
        
        # Ferma scheduler
        if self.scheduler:
            await self.scheduler.stop()
        
        # Cancella task pendenti
        for task in self.async_tasks:
            if not task.done():
                task.cancel()
        
        # Aspetta completamento task
        if self.async_tasks:
            await asyncio.gather(*self.async_tasks, return_exceptions=True)
        
        # Chiudi connessioni
        await self.container.close()
        
        self.state.is_running = False
        logger.info("Engine spento")
    
    async def run_full_check(self):
        """
        Esegue un controllo completo del portafoglio:
        1. Aggiorna prezzi
        2. Recupera news
        3. Analizza ogni posizione con AI
        4. Verifica stop-loss/take-profit
        5. Genera notifiche
        """
        if not self.state.is_running:
            logger.warning("Engine non in esecuzione, skip check")
            return
        
        logger.info("Avvio controllo completo portafoglio...")
        start_time = datetime.now()
        
        try:
            # 1. Aggiorna prezzi di mercato
            await self._update_market_prices()
            
            # 2. Recupera news e sentiment
            await self._fetch_market_news()
            
            # 3. Analizza posizioni aperte
            await self._analyze_open_positions()
            
            # 4. Verifica stop-loss e take-profit
            await self._check_thresholds()
            
            # 5. Genera notifiche se necessario
            await self._generate_notifications()
            
            # Aggiorna stato
            self.state.last_check = datetime.now()
            self.state.next_check = datetime.now() + timedelta(
                minutes=self.container.settings.monitoring_interval_minutes
            )
            self.state.total_analyses += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Controllo completato in {duration:.2f}s")
            
            # Emetti segnale per UI (implementato con callback)
            if hasattr(self, 'on_check_completed'):
                await self.on_check_completed(self.state)
            
        except Exception as e:
            logger.error(f"Errore durante controllo portafoglio: {e}")
            self.state.errors_count += 1
    
    async def _update_market_prices(self):
        """Aggiorna i prezzi correnti di mercato"""
        logger.debug("Aggiornamento prezzi di mercato...")
        
        try:
            portfolio = await self.container.portfolio_manager.get_portfolio()
            
            for holding in portfolio:
                if holding.status == "open":
                    # Ottieni prezzo corrente dal provider market data
                    price_data = await self.container.market_data.get_current_price(
                        holding.asset
                    )
                    
                    if price_data:
                        holding.current_price = price_data.price
                        holding.last_updated = datetime.now()
                        
                        # Aggiorna nel database
                        await self.container.portfolio_manager.update_holding(holding)
                        
                        logger.debug(
                            f"Prezzo aggiornato: {holding.asset} = {price_data.price}"
                        )
                        
        except Exception as e:
            logger.error(f"Errore aggiornamento prezzi: {e}")
            raise
    
    async def _fetch_market_news(self):
        """Recupera news e sentiment di mercato"""
        logger.debug("Recupero news di mercato...")
        
        try:
            # Ottieni asset con posizioni aperte
            open_assets = await self.container.portfolio_manager.get_open_assets()
            
            for asset in open_assets[:5]:  # Limita a 5 asset per non sovraccaricare
                news = await self.container.market_data.get_news(asset, limit=3)
                sentiment = await self.container.market_data.get_sentiment(asset)
                
                # Salva in cache per uso successivo nelle analisi
                await self.container.market_data.cache_news_sentiment(
                    asset, news, sentiment
                )
                
        except Exception as e:
            logger.error(f"Errore recupero news: {e}")
            # Non critico, continua
    
    async def _analyze_open_positions(self):
        """Analizza ogni posizione aperta con AI"""
        logger.debug("Analisi posizioni aperte con AI...")
        
        try:
            open_holdings = await self.container.portfolio_manager.get_open_holdings()
            
            for holding in open_holdings:
                # Costruisci prompt strutturato
                prompt_data = await PromptManager.build_analysis_prompt(
                    holding=holding,
                    market_data=self.container.market_data,
                    profile=self.container.settings.default_prompt_profile
                )
                
                # Crea richiesta AI
                ai_request = AIRequest(
                    system_prompt=prompt_data.system_prompt,
                    user_prompt=prompt_data.user_prompt,
                    temperature=self.container.settings.ai_temperature,
                    max_tokens=self.container.settings.ai_max_tokens
                )
                
                # Ottieni analisi dal provider AI
                ai_provider = self.container.ai_provider
                analysis = await ai_provider.analyze_position(ai_request)
                
                # Salva analisi nello storico
                await self._save_analysis(holding, analysis)
                
                # Notifica se necessario
                if analysis.decision in ["SELL", "REDUCE_POSITION"]:
                    await self.container.notifications.send_notification(
                        title=f"⚠️ Azione suggerita: {analysis.decision}",
                        message=f"{holding.asset}: {analysis.motivation}",
                        notification_type="ai_suggestion"
                    )
                
                logger.info(
                    f"Analisi completata: {holding.asset} -> {analysis.decision} "
                    f"(confidenza: {analysis.probability}%)"
                )
                
        except Exception as e:
            logger.error(f"Errore analisi posizioni: {e}")
            raise
    
    async def _check_thresholds(self):
        """Verifica stop-loss e take-profit per tutte le posizioni"""
        logger.debug("Verifica soglie stop-loss/take-profit...")
        
        try:
            open_holdings = await self.container.portfolio_manager.get_open_holdings()
            
            for holding in open_holdings:
                # Calcola P&L
                pnl_pct = holding.calculate_profit_percentage()
                
                # Verifica stop-loss (default -10%)
                stop_loss = holding.stop_loss or -10.0
                if pnl_pct <= stop_loss:
                    await self.container.notifications.send_notification(
                        title="🛑 STOP LOSS RAGGIUNTO",
                        message=f"{holding.asset} ha raggiunto stop loss: {pnl_pct:.2f}%",
                        notification_type="alert",
                        urgent=True
                    )
                
                # Verifica take-profit (default +20%)
                take_profit = holding.take_profit or 20.0
                if pnl_pct >= take_profit:
                    await self.container.notifications.send_notification(
                        title="✅ TAKE PROFIT RAGGIUNTO",
                        message=f"{holding.asset} ha raggiunto take profit: {pnl_pct:.2f}%",
                        notification_type="alert",
                        urgent=True
                    )
                    
        except Exception as e:
            logger.error(f"Errore verifica soglie: {e}")
    
    async def _generate_notifications(self):
        """Genera notifiche basate sullo stato del portafoglio"""
        logger.debug("Generazione notifiche...")
        
        try:
            # Verifica performance giornaliera
            daily_pnl = await self.container.portfolio_manager.get_daily_pnl()
            
            if abs(daily_pnl.percentage) > 5:
                emoji = "📈" if daily_pnl.percentage > 0 else "📉"
                await self.container.notifications.send_notification(
                    title=f"{emoji} Performance giornaliera significativa",
                    message=(
                        f"P&L giornaliero: {daily_pnl.amount:.2f}€ "
                        f"({daily_pnl.percentage:+.2f}%)"
                    ),
                    notification_type="performance"
                )
                
        except Exception as e:
            logger.error(f"Errore generazione notifiche: {e}")
    
    async def _save_analysis(self, holding: PortfolioHolding, analysis):
        """Salva analisi AI nel database"""
        try:
            analysis_record = AnalysisHistory(
                holding_id=holding.id,
                provider=self.container.settings.ai_provider,
                model=self.container.settings.ai_model,
                request_prompt="",  # Sarebbe meglio salvare il prompt completo
                response_raw=str(analysis.dict()),
                decision=analysis.decision,
                probability=analysis.probability,
                risk_level=analysis.risk_level,
                targets=analysis.targets,
                stop_loss_suggested=analysis.stop_loss
            )
            
            await self.container.database.add(analysis_record)
            await self.container.database.commit()
            
        except Exception as e:
            logger.error(f"Errore salvataggio analisi: {e}")
    
    async def _load_settings(self):
        """Carica impostazioni dal database"""
        try:
            db_settings = await self.container.database.get_all_settings()
            
            for setting in db_settings:
                if hasattr(self.container.settings, setting.key):
                    setattr(self.container.settings, setting.key, setting.value)
                    
        except Exception as e:
            logger.warning(f"Errore caricamento impostazioni: {e}")
    
    async def process_async_tasks(self):
        """Processa task asincroni pendenti (chiamato dal timer Qt)"""
        # Questo metodo viene chiamato periodicamente dal timer Qt
        # per processare eventuali task asincroni in sospeso
        pass
    
    # Metodi per controllo manuale
    async def start_monitoring(self):
        """Avvia monitoraggio automatico"""
        if not self.state.is_monitoring:
            await self.scheduler.start(
                self.container.settings.monitoring_interval_minutes
            )
            self.state.is_monitoring = True
            logger.info("Monitoraggio avviato")
    
    async def stop_monitoring(self):
        """Ferma monitoraggio automatico"""
        if self.state.is_monitoring:
            await self.scheduler.stop()
            self.state.is_monitoring = False
            logger.info("Monitoraggio fermato")
    
    async def pause_monitoring(self):
        """Mette in pausa il monitoraggio"""
        if self.state.is_monitoring:
            await self.scheduler.pause()
            logger.info("Monitoraggio in pausa")
    
    async def resume_monitoring(self):
        """Riprende il monitoraggio"""
        if self.state.is_monitoring:
            await self.scheduler.resume()
            logger.info("Monitoraggio ripreso")
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Ottiene riepilogo portafoglio per UI"""
        return await self.container.portfolio_manager.get_summary()
    
    async def analyze_single_position(self, holding_id: int) -> Optional[Dict]:
        """Analizza una singola posizione"""
        holding = await self.container.portfolio_manager.get_holding(holding_id)
        
        if not holding:
            return None
        
        prompt_data = await PromptManager.build_analysis_prompt(
            holding=holding,
            market_data=self.container.market_data
        )
        
        ai_request = AIRequest(
            system_prompt=prompt_data.system_prompt,
            user_prompt=prompt_data.user_prompt
        )
        
        analysis = await self.container.ai_provider.analyze_position(ai_request)
        await self._save_analysis(holding, analysis)
        
        return analysis.dict()