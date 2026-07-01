"""
Gestore prompt per AI
Costruisce prompt strutturati per analisi trading
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from loguru import logger


@dataclass
class PromptData:
    """Dati per costruzione prompt"""
    system_prompt: str
    user_prompt: str
    context: Dict[str, Any]


class PromptManager:
    """Gestisce creazione e personalizzazione prompt AI"""
    
    # Profili predefiniti
    PROFILES = {
        "swing_trader": {
            "name": "Swing Trading Expert",
            "description": "Esperto in swing trading con orizzonte temporale di giorni/settimane",
            "expertise": [
                "Analisi tecnica avanzata",
                "Pattern riconoscimento",
                "Swing trading strategies",
                "Risk management"
            ],
            "focus": "Identificare movimenti di prezzo di medio termine",
            "timeframe": "3-30 giorni"
        },
        "day_trader": {
            "name": "Day Trading Expert",
            "description": "Esperto in day trading con focus intraday",
            "expertise": [
                "Price action",
                "Order flow analysis",
                "Scalping strategies",
                "Volume analysis"
            ],
            "focus": "Movimenti intraday e breakout",
            "timeframe": "Minuti-ore"
        },
        "crypto_expert": {
            "name": "Crypto Expert",
            "description": "Esperto in criptovalute e mercati digitali",
            "expertise": [
                "On-chain analysis",
                "DeFi protocols",
                "Tokenomics",
                "Crypto market cycles"
            ],
            "focus": "Analisi mercato crypto e trend",
            "timeframe": "Variabile"
        },
        "etf_expert": {
            "name": "ETF Expert",
            "description": "Specialista in ETF e fondi indicizzati",
            "expertise": [
                "ETF analysis",
                "Sector rotation",
                "Index tracking",
                "Expense ratio analysis"
            ],
            "focus": "Analisi ETF e allocazione",
            "timeframe": "Medio-lungo termine"
        },
        "value_investor": {
            "name": "Value Investing Expert",
            "description": "Esperto in value investing alla Warren Buffett",
            "expertise": [
                "Fundamental analysis",
                "DCF valuation",
                "Margin of safety",
                "Competitive advantage analysis"
            ],
            "focus": "Valore intrinseco e lungo termine",
            "timeframe": "1-5 anni"
        }
    }
    
    @classmethod
    async def build_analysis_prompt(cls, holding, market_data, 
                                   profile: str = "swing_trader") -> PromptData:
        """
        Costruisce prompt per analisi posizione
        
        Args:
            holding: Posizione da analizzare
            market_data: Provider dati di mercato
            profile: Profilo di analisi
            
        Returns:
            PromptData con system e user prompt
        """
        profile_config = cls.PROFILES.get(profile, cls.PROFILES["swing_trader"])
        
        # Costruisci system prompt
        system_prompt = cls._build_system_prompt(profile_config)
        
        # Ottieni dati di mercato aggiuntivi
        market_info = await cls._get_market_info(holding.asset, market_data)
        
        # Costruisci user prompt
        user_prompt = cls._build_user_prompt(holding, market_info, profile_config)
        
        return PromptData(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context={
                "holding_id": holding.id if hasattr(holding, 'id') else None,
                "asset": holding.asset if hasattr(holding, 'asset') else holding.get('asset'),
                "profile": profile
            }
        )
    
    @classmethod
    async def build_portfolio_analysis_prompt(cls, portfolio: Dict[str, Any],
                                             market_data) -> PromptData:
        """
        Costruisce prompt per analisi portfolio completo
        
        Args:
            portfolio: Dati portafoglio
            market_data: Provider dati di mercato
            
        Returns:
            PromptData
        """
        system_prompt = (
            "Sei un analista finanziario esperto. Analizza il portafoglio completo, "
            "valutando diversificazione, rischio complessivo e performance. "
            "Fornisci raccomandazioni specifiche per ottimizzare il portafoglio."
        )
        
        user_prompt = f"""
        Analizza il seguente portafoglio:
        
        Valore totale: €{portfolio.get('total_value', 0):,.2f}
        Numero posizioni: {portfolio.get('open_positions', 0)}
        Performance totale: {portfolio.get('total_pnl_pct', 0):+.2f}%
        
        Posizioni:
        {cls._format_holdings(portfolio.get('holdings', []))}
        
        Fornisci:
        1. Valutazione diversificazione
        2. Analisi rischio complessivo
        3. Suggerimenti ribilanciamento
        4. Raccomandazioni specifiche
        """
        
        return PromptData(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context={"type": "portfolio_analysis"}
        )
    
    @classmethod
    async def build_opportunity_search_prompt(cls, portfolio: Dict[str, Any],
                                             market_data, criteria: Dict = None) -> PromptData:
        """
        Costruisce prompt per ricerca opportunità
        
        Args:
            portfolio: Portafoglio attuale
            market_data: Dati di mercato
            criteria: Criteri di ricerca
            
        Returns:
            PromptData
        """
        system_prompt = (
            "Sei un esperto nella ricerca di opportunità di investimento. "
            "Analizza il mercato e suggerisci asset che completerebbero il portafoglio attuale."
        )
        
        user_prompt = f"""
        Portfolio attuale:
        {cls._format_holdings(portfolio.get('holdings', []))}
        
        Criteri ricerca: {json.dumps(criteria) if criteria else 'Bilanciati'}
        
        Suggerisci 3-5 opportunità specificando:
        1. Asset e motivo
        2. Punti di forza
        3. Rischi
        4. Target price
        5. Dimensione posizione suggerita
        """
        
        return PromptData(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context={"type": "opportunity_search"}
        )
    
    @classmethod
    async def build_post_trade_analysis_prompt(cls, trade: Dict[str, Any]) -> PromptData:
        """
        Costruisce prompt per analisi post-trade
        
        Args:
            trade: Dati trade chiuso
            
        Returns:
            PromptData
        """
        system_prompt = (
            "Sei un analista che valuta la qualità delle operazioni di trading. "
            "Analizza obiettivamente i risultati e suggerisci miglioramenti."
        )
        
        user_prompt = f"""
        Analizza questa operazione chiusa:
        
        Asset: {trade.get('asset')}
        Entrata: €{trade.get('entry_price'):.2f}
        Uscita: €{trade.get('exit_price'):.2f}
        Quantità: {trade.get('quantity')}
        P&L: €{trade.get('pnl_eur', 0):+,.2f} ({trade.get('pnl_pct', 0):+.2f}%)
        Durata: {trade.get('holding_period_days', 'N/A')} giorni
        
        Valuta:
        1. Qualità dell'operazione (eccellente/buona/media/scarsa)
        2. Punti di forza
        3. Aree di miglioramento
        4. Lezioni apprese
        """
        
        return PromptData(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context={"type": "post_trade_analysis"}
        )
    
    @classmethod
    def _build_system_prompt(cls, profile: Dict[str, str]) -> str:
        """Costruisce system prompt dal profilo"""
        return f"""
        Sei un {profile['name']}.
        {profile['description']}
        
        Expertise:
        {chr(10).join(f'- {exp}' for exp in profile['expertise'])}
        
        Focus: {profile['focus']}
        Orizzonte temporale: {profile['timeframe']}
        
        IMPORTANTE: 
        - Rispondi SEMPRE in formato JSON strutturato
        - Includi sempre decision, motivation, probability, risk_level
        - Fornisci analisi dettagliate ma concise
        - NON eseguire mai operazioni automaticamente
        """
    
    @classmethod
    def _build_user_prompt(cls, holding, market_info: Dict[str, Any],
                          profile: Dict[str, str]) -> str:
        """Costruisce user prompt con dati posizione"""
        
        # Estrai dati holding
        if hasattr(holding, 'to_dict'):
            h = holding.to_dict()
        else:
            h = holding
            
        asset = h.get('asset', h.get('symbol', 'Unknown'))
        quantity = h.get('quantity', 0)
        entry_price = h.get('entry_price', 0)
        current_price = h.get('current_price', 0)
        profit_eur = h.get('profit_eur', 0)
        profit_pct = h.get('profit_pct', 0)
        
        prompt = f"""
        Analizza questa posizione e fornisci una raccomandazione:
        
        Asset: {asset}
        Quantità: {quantity}
        Prezzo entrata: €{entry_price:.2f}
        Prezzo corrente: €{current_price:.2f}
        Profitto: €{profit_eur:+,.2f} ({profit_pct:+.2f}%)
        
        Dati di mercato:
        """
        
        # Aggiungi dati mercato se disponibili
        if market_info:
            if 'rsi' in market_info:
                prompt += f"- RSI: {market_info['rsi']:.1f}\n"
            if 'macd' in market_info:
                prompt += f"- MACD: {market_info['macd']}\n"
            if 'volume' in market_info:
                prompt += f"- Volume: {market_info['volume']}\n"
            if 'volatility' in market_info:
                prompt += f"- Volatilità: {market_info['volatility']:.2f}%\n"
            if 'news_sentiment' in market_info:
                prompt += f"- Sentiment news: {market_info['news_sentiment']}\n"
        
        prompt += f"""
        Orizzonte temporale: {profile['timeframe']}
        
        Rispondi con un JSON contenente:
        {{
            "decision": "HOLD|BUY|SELL|REDUCE_POSITION|INCREASE_POSITION",
            "motivation": "spiegazione dettagliata",
            "probability": numero (0-100),
            "risk_level": "low|medium|high|very_high",
            "strengths": ["punto di forza 1", ...],
            "weaknesses": ["punto debole 1", ...],
            "targets": [prezzo_target_1, ...],
            "stop_loss": prezzo_stop_suggerito,
            "timeframe": "short_term|medium_term|long_term",
            "key_indicators": {{"rsi": valore, "trend": "bullish|bearish|neutral"}}
        }}
        """
        
        return prompt
    
    @classmethod
    async def _get_market_info(cls, asset: str, market_data) -> Dict[str, Any]:
        """
        Ottiene informazioni di mercato per un asset
        
        Args:
            asset: Simbolo asset
            market_data: Provider market data
            
        Returns:
            Dizionario con dati mercato
        """
        try:
            info = {}
            
            # Prezzo corrente
            price = await market_data.get_current_price(asset)
            if price:
                info['current_price'] = price.price
            
            # Indicatori tecnici
            indicators = await market_data.get_technical_indicators(asset)
            if indicators:
                info.update(indicators)
            
            # News sentiment
            sentiment = await market_data.get_sentiment(asset)
            if sentiment:
                info['news_sentiment'] = sentiment
            
            return info
            
        except Exception as e:
            logger.warning(f"Errore recupero dati mercato per {asset}: {e}")
            return {}
    
    @classmethod
    def _format_holdings(cls, holdings: List[Dict]) -> str:
        """Formatta lista holdings per prompt"""
        formatted = []
        for h in holdings[:10]:  # Limita a 10 per non superare limiti token
            asset = h.get('asset', 'Unknown')
            pnl = h.get('profit_pct', 0)
            weight = h.get('weight', 0)
            formatted.append(
                f"- {asset}: €{h.get('current_price', 0)*h.get('quantity', 0):,.2f} "
                f"({weight:.1f}% portfolio) | P&L: {pnl:+.2f}%"
            )
        return '\n'.join(formatted)
    
    @classmethod
    def get_profile_names(cls) -> List[str]:
        """Ottiene lista nomi profili disponibili"""
        return [p['name'] for p in cls.PROFILES.values()]
    
    @classmethod
    def create_custom_profile(cls, name: str, description: str, expertise: List[str],
                            focus: str, timeframe: str) -> Dict[str, Any]:
        """
        Crea un profilo personalizzato
        
        Args:
            name: Nome profilo
            description: Descrizione
            expertise: Lista competenze
            focus: Focus analisi
            timeframe: Orizzonte temporale
            
        Returns:
            Profilo creato
        """
        profile = {
            "name": name,
            "description": description,
            "expertise": expertise,
            "focus": focus,
            "timeframe": timeframe
        }
        return profile