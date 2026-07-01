"""
AI Module
Provider AI e gestione prompt
"""

from .base import AbstractAIProvider, AIRequest, AIResponse
from .prompt_manager import PromptManager

__all__ = ['AbstractAIProvider', 'AIRequest', 'AIResponse', 'PromptManager']