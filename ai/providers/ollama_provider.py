"""
Provider Ollama - Modelli locali
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


class OllamaProvider(AbstractAIProvider):
    """Provider per modelli Ollama locali"""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "llama3", temperature: float = 0.7,
                 max_tokens: int = 1500, **kwargs):
        super().__init__(api_key=None, model=model, temperature=temperature,
                        max_tokens=max_tokens, **kwargs)
        
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(300))  # Timeout più lungo per modelli locali
        
        logger.info(f"Ollama Provider inizializzato: url={base_url}, model={model}")
    
    async def analyze_position(self, request: AIRequest) -> AIResponse:
        """Analizza posizione con modello locale"""
        start_time = time.time()
        
        try:
            full_prompt = f"{request.system_prompt}\n\n{request.user_prompt}"
            full_prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON. No other text."
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": request.temperature,
                    "stream": False,
                    "options": {
                        "num_predict": request.max_tokens
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API Error: {response.text}")
            
            data = response.json()
            content = data.get("response", "")
            parsed = self._parse_response_to_json(content)
            
            execution_time = (time.time() - start_time) * 1000
            
            return AIResponse(
                decision=DecisionType(parsed.get("decision", "HOLD")),
                motivation=parsed.get("motivation", ""),
                probability=float(parsed.get("probability", 50)),
                risk_level=RiskLevel(parsed.get("risk_level", "medium")),
                strengths=parsed.get("strengths", []),
                weaknesses=parsed.get("weaknesses", []),
                targets=parsed.get("targets", []),
                stop_loss=parsed.get("stop_loss"),
                raw_text=content,
                execution_time_ms=execution_time,
                token_usage={
                    "total_tokens": data.get("eval_count", 0),
                    "tokens_per_second": data.get("eval_duration", 0) / 1e9 if data.get("eval_duration") else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Errore analisi Ollama: {e}")
            raise
    
    async def generate_text(self, prompt: str, system: str = "",
                           context: List[Dict[str, str]] = None) -> str:
        """Genera testo con modello locale"""
        try:
            if system:
                prompt = f"System: {system}\n\nUser: {prompt}"
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "stream": False,
                    "options": {
                        "num_predict": self.max_tokens
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                raise Exception(f"Error: {response.text}")
                
        except Exception as e:
            logger.error(f"Errore generazione Ollama: {e}")
            return f"Errore modello locale: {str(e)}"
    
    async def analyze_market(self, asset: str, indicators: Dict[str, Any]) -> AIResponse:
        """Analisi mercato"""
        request = AIRequest(
            system_prompt="Analista tecnico. Rispondi in JSON.",
            user_prompt=f"Analisi per {asset}: {json.dumps(indicators)}"
        )
        return await self.analyze_position(request)
    
    async def suggest_opportunities(self, portfolio: Dict[str, Any],
                                   market_data: Dict[str, Any],
                                   risk_profile: str = "moderate") -> List[Dict[str, Any]]:
        """Suggerisci opportunità"""
        response = await self.generate_text(
            prompt=f"Portfolio: {json.dumps(portfolio)}\nRisk: {risk_profile}\nSuggerisci opportunità di investimento.",
            system="Sei un consulente finanziario esperto."
        )
        
        try:
            return json.loads(response)
        except:
            return [{"suggestion": response}]
    
    async def get_available_models(self) -> List[str]:
        """Ottieni modelli disponibili localmente"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
        except Exception as e:
            logger.warning(f"Impossibile recuperare modelli Ollama: {e}")
        
        return [self.model]
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Scarica un modello
        
        Args:
            model_name: Nome modello da scaricare
            
        Returns:
            True se scaricato con successo
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600  # Timeout lungo per download
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Errore download modello {model_name}: {e}")
            return False
    
    async def close(self):
        """Chiude client"""
        await self.client.aclose()