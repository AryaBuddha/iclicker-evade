"""AI services for iClicker Evade.

This package provides AI-powered answer suggestion services
using various AI models like OpenAI GPT-4 Vision, Google Gemini, and Anthropic Claude.
"""

from .base_ai_service import BaseAIService, AIAnswerSuggestion, AIServiceError
from .openai_service import OpenAIAnswerService, create_openai_service
from .gemini_service import GeminiAnswerService, create_gemini_service
from .claude_service import ClaudeAnswerService, create_claude_service

__all__ = [
    "BaseAIService",
    "AIAnswerSuggestion",
    "AIServiceError",
    "OpenAIAnswerService",
    "create_openai_service",
    "GeminiAnswerService",
    "create_gemini_service",
    "ClaudeAnswerService",
    "create_claude_service",
]