"""Claude-based AI service for answer suggestions.

This module provides Anthropic Claude integration for analyzing
iClicker question screenshots and providing answer suggestions.
"""

import base64
import time
from typing import Optional
import asyncio
import logging

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

from .base_ai_service import BaseAIService, AIAnswerSuggestion, AIServiceError

class ClaudeAnswerService(BaseAIService):
    """Anthropic Claude service for iClicker answer suggestions.

    Uses Claude to analyze question screenshots and provide suggestions.
    """

    SUPPORTED_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    DEFAULT_MODEL = "claude-3-haiku-20240307"

    def __init__(self, api_key: str, model_name: Optional[str] = None) -> None:
        """Initialize the Claude service.

        Args:
            api_key: Anthropic API key
            model_name: Specific Claude model to use

        Raises:
            AIServiceError: If Claude is not available or initialization fails
        """
        if not CLAUDE_AVAILABLE:
            raise AIServiceError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        model_name = model_name or self.DEFAULT_MODEL
        super().__init__(api_key, model_name)

        if model_name not in self.SUPPORTED_MODELS:
            self.logger.warning(f"Model {model_name} not in supported list. Proceeding anyway.")

        try:
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except Exception as e:
            raise AIServiceError(f"Failed to initialize Claude client: {e}") from e

    async def analyze_question(self, image_path: str, question_text: str = "") -> AIAnswerSuggestion:
        """Analyze a question image using Claude.

        Args:
            image_path: Path to the question screenshot
            question_text: Optional extracted text from the question

        Returns:
            AIAnswerSuggestion with Claude's recommended answer

        Raises:
            AIServiceError: If analysis fails
        """
        start_time = time.time()

        try:
            base64_image = self._encode_image(image_path)
            prompt = self._create_analysis_prompt(question_text)

            message = await self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            suggestion = self._parse_response(message, time.time() - start_time)

            self.logger.info(f"Claude analysis completed: {suggestion.suggested_answer} ({suggestion.confidence_percentage})")
            return suggestion

        except Exception as e:
            self.logger.error(f"Claude analysis failed: {e}")
            raise AIServiceError(f"Failed to analyze question with Claude: {e}") from e

    async def test_connection(self) -> bool:
        """Test the connection to Claude API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            await self.client.count_tokens(model=self.model_name, text="test")
            return True
        except Exception as e:
            self.logger.error(f"Claude connection test failed: {e}")
            return False

    @property
    def service_name(self) -> str:
        """Get the name of this AI service."""
        return "Anthropic Claude"

    @property
    def supported_models(self) -> list:
        """Get list of supported Claude models."""
        return self.SUPPORTED_MODELS.copy()

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _create_analysis_prompt(self, question_text: str = "") -> str:
        """Create the analysis prompt for Claude."""
        base_prompt = """You are an AI assistant helping with iClicker multiple choice questions.
Analyze the provided screenshot of an iClicker question and provide the best answer.

Your response must be in the following JSON format:
{
    "answer": "A|B|C|D|E",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this answer is correct"
}

Guidelines:
- Choose the most accurate answer based on the question content
- Confidence should reflect how certain you are (1.0 = completely certain, 0.5 = moderate certainty)
- Reasoning should be concise but explain your logic
- If the question is unclear or you cannot determine the answer, choose your best guess with lower confidence
"""
        if question_text:
            base_prompt += f"\nExtracted question text (if helpful): {question_text}\n"
        return base_prompt

    def _parse_response(self, response, processing_time: float) -> AIAnswerSuggestion:
        """Parse Claude response into AIAnswerSuggestion."""
        try:
            import json
            response_text = response.content[0].text.strip()

            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text

            data = json.loads(json_str)

            answer = data.get("answer", "").upper()
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "No reasoning provided")

            if answer not in ['A', 'B', 'C', 'D', 'E']:
                for char in response_text.upper():
                    if char in ['A', 'B', 'C', 'D', 'E']:
                        answer = char
                        reasoning = f"Extracted '{char}' from response: {reasoning}"
                        break
                else:
                    answer = "C"
                    confidence = 0.1
                    reasoning = f"Could not parse answer. Defaulting to C. Original: {response_text[:100]}"

            return AIAnswerSuggestion(
                suggested_answer=answer,
                confidence=confidence,
                reasoning=reasoning,
                model_used=self.model_name,
                processing_time=processing_time
            )
        except Exception as e:
            self.logger.error(f"Failed to parse Claude response: {e}")
            return AIAnswerSuggestion(
                suggested_answer="C",
                confidence=0.1,
                reasoning=f"Failed to parse AI response. Error: {str(e)}",
                model_used=self.model_name,
                processing_time=processing_time
            )

def create_claude_service(api_key: Optional[str], model_name: Optional[str] = None) -> Optional[ClaudeAnswerService]:
    """Factory function to create a Claude service.

    Args:
        api_key: Anthropic API key (can be None to disable AI)
        model_name: Specific model to use (optional)

    Returns:
        ClaudeAnswerService instance if key provided, None otherwise
    """
    if not api_key:
        return None

    try:
        return ClaudeAnswerService(api_key, model_name)
    except AIServiceError as e:
        logging.error(f"Failed to create Claude service: {e}")
        return None