"""
Provider Anthropic (Claude)
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


class AnthropicProvider(AbstractAIProvider):
    """Provider per Anthropic Claude models"""
    
    MODELS = {
        "claude-3-opus-20240229": {"max_tokens": 200000, "cost_per_1k_input": 0.015, "cost_per_1k_output": 0.075},
        "claude-3-sonnet-20240229": {"max_tokens": 200000, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015},
        "claude-3-haiku-20240307": {"max_tokens": 200000, "cost_per_1k_input": 0.00025, "cost_per_1k_output": 0.00125},
    }
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229",
                 temperature: float = 0.7, max_tokens: int = 1500,
                 timeout: int = 30, **kwargs):
        super().__init__(api_key, model, temperature, max_tokens, timeout, **kwargs)
        
        self.base_url = "https://api.anthropic.com/v1"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"Anthropic Provider inizializzato: model={model}")
    
    async def analyze_position(self, request: AIRequest) -> AIResponse:
        """Analizza posizione con Claude"""
        start_time = time.time()
        
        try:
            system_prompt = request.system_prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON."
            
            response = await self.client.post(
                f"{self.base_url}/messages",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": request.user_prompt}
                    ],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.json()}")
            
            data = response.json()
            content = data["content"][0]["text"]
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
                    "input": data.get("usage", {}).get("input_tokens", 0),
                    "output": data.get("usage", {}).get("output_tokens", 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Errore analisi Anthropic: {e}")
            raise
    
    async def generate_text(self, prompt: str, system: str = "",
                           context: List[Dict[str, str]] = None) -> str:
        """Genera testo con Claude"""
        try:
            messages = []
            
            if context:
                for msg in context:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.post(
                f"{self.base_url}/messages",
                json={
                    "model": self.model,
                    "system": system,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                raise Exception(f"API Error: {response.text}")
                
        except Exception as e:
            logger.error(f"Errore generazione Anthropic: {e}")
            return f"Errore: {str(e)}"
    
    async def analyze_market(self, asset: str, indicators: Dict[str, Any]) -> AIResponse:
        """Analizza mercato"""
        request = AIRequest(
            system_prompt="Sei un analista tecnico. Fornisci analisi in JSON.",
            user_prompt=f"Analizza {asset} con questi indicatori: {json.dumps(indicators)}"
        )
        return await self.analyze_position(request)
    
    async def suggest_opportunities(self, portfolio: Dict[str, Any],
                                   market_data: Dict[str, Any],
                                   risk_profile: str = "moderate") -> List[Dict[str, Any]]:
        """Suggerisce opportunità"""
        response = await self.generate_text(
            prompt=f"Portfolio: {json.dumps(portfolio)}\nRisk: {risk_profile}\nSuggest opportunities.",
            system="You are an investment advisor. Suggest 3-5 opportunities."
        )
        
        try:
            return json.loads(response)
        except:
            return [{"suggestion": response}]
    
    async def close(self):
        """Chiude client"""
        await self.client.aclose()