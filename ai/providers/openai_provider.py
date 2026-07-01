"""
Provider OpenAI - Implementazione con API OpenAI
"""

import json
import time
from typing import Dict, Any, List, Optional
import httpx

from loguru import logger

from ai.base import (
    AbstractAIProvider, AIRequest, AIResponse,
    DecisionType, RiskLevel
)


class OpenAIProvider(AbstractAIProvider):
    """Provider per OpenAI GPT models"""
    
    MODELS = {
        "gpt-4o": {"max_tokens": 128000, "cost_per_1k_input": 0.005, "cost_per_1k_output": 0.015},
        "gpt-4-turbo": {"max_tokens": 128000, "cost_per_1k_input": 0.01, "cost_per_1k_output": 0.03},
        "gpt-4": {"max_tokens": 8192, "cost_per_1k_input": 0.03, "cost_per_1k_output": 0.06},
        "gpt-3.5-turbo": {"max_tokens": 16385, "cost_per_1k_input": 0.0005, "cost_per_1k_output": 0.0015},
    }
    
    def __init__(self, api_key: str, model: str = "gpt-4o", 
                 temperature: float = 0.7, max_tokens: int = 1500,
                 timeout: int = 30, **kwargs):
        super().__init__(api_key, model, temperature, max_tokens, timeout, **kwargs)
        
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"OpenAI Provider inizializzato: model={model}")
    
    async def analyze_position(self, request: AIRequest) -> AIResponse:
        """Analizza posizione e restituisce decisione"""
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt}
            ]
            
            response = await self._make_request(messages, request.temperature, request.max_tokens)
            
            content = response["choices"][0]["message"]["content"]
            parsed = self._parse_response_to_json(content)
            
            execution_time = (time.time() - start_time) * 1000
            
            return AIResponse(
                decision=DecisionType(parsed.get("decision", "HOLD")),
                motivation=parsed.get("motivation", "No motivation provided"),
                probability=float(parsed.get("probability", 50)),
                risk_level=RiskLevel(parsed.get("risk_level", "medium")),
                strengths=parsed.get("strengths", []),
                weaknesses=parsed.get("weaknesses", []),
                targets=parsed.get("targets", []),
                stop_loss=parsed.get("stop_loss"),
                timeframe=parsed.get("timeframe", "medium_term"),
                key_indicators=parsed.get("key_indicators", {}),
                raw_text=content,
                token_usage=response.get("usage", {}),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Errore analisi OpenAI: {e}")
            raise
    
    async def generate_text(self, prompt: str, system: str = "",
                           context: List[Dict[str, str]] = None) -> str:
        """Genera testo per conversazione"""
        try:
            messages = []
            
            if system:
                messages.append({"role": "system", "content": system})
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self._make_request(
                messages, 
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                json_mode=False
            )
            
            return response["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Errore generazione testo OpenAI: {e}")
            return f"Errore nella generazione della risposta: {str(e)}"
    
    async def analyze_market(self, asset: str, indicators: Dict[str, Any]) -> AIResponse:
        """Analizza condizioni mercato"""
        prompt = f"""
        Analizza le condizioni di mercato per {asset} con questi indicatori:
        {json.dumps(indicators, indent=2)}
        
        Fornisci una valutazione completa in formato JSON.
        """
        
        request = AIRequest(
            system_prompt="Sei un analista tecnico esperto. Rispondi in JSON.",
            user_prompt=prompt,
            temperature=0.5,
            max_tokens=1000
        )
        
        return await self.analyze_position(request)
    
    async def suggest_opportunities(self, portfolio: Dict[str, Any],
                                   market_data: Dict[str, Any],
                                   risk_profile: str = "moderate") -> List[Dict[str, Any]]:
        """Suggerisce opportunità di investimento"""
        prompt = f"""
        Basandoti su questo portafoglio e dati di mercato, suggerisci 3-5 opportunità:
        
        Portfolio: {json.dumps(portfolio, indent=2)}
        Profilo rischio: {risk_profile}
        
        Per ogni opportunità fornisci:
        - asset
        - motivazione
        - target price
        - stop loss
        - dimensione posizione suggerita (%)
        """
        
        response = await self.generate_text(
            prompt=prompt,
            system="Sei un esperto nella ricerca di opportunità di investimento."
        )
        
        try:
            suggestions = json.loads(response)
            return suggestions if isinstance(suggestions, list) else [suggestions]
        except:
            return [{"raw_suggestion": response}]
    
    async def _make_request(self, messages: List[Dict], temperature: float,
                           max_tokens: int, json_mode: bool = True) -> Dict[str, Any]:
        """Effettua richiesta API OpenAI"""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode and "gpt-4" in self.model or "gpt-3.5" in self.model:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise Exception(f"API Error: {error_data.get('error', {}).get('message', 'Unknown')}")
            
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(f"Timeout richiesta OpenAI ({self.timeout}s)")
            raise Exception(f"Timeout dopo {self.timeout} secondi")
        except Exception as e:
            logger.error(f"Errore richiesta OpenAI: {e}")
            raise
    
    async def get_available_models(self) -> List[str]:
        """Ottiene modelli disponibili"""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            if response.status_code == 200:
                models = response.json().get("data", [])
                gpt_models = [m["id"] for m in models if m["id"].startswith("gpt")]
                return gpt_models
        except Exception as e:
            logger.warning(f"Errore recupero modelli: {e}")
        
        return list(self.MODELS.keys())
    
    async def close(self):
        """Chiude client HTTP"""
        await self.client.aclose()