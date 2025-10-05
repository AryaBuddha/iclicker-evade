"""Gemini-based AI service for answer suggestions.

This module provides Google Gemini integration for analyzing
iClicker question screenshots and providing answer suggestions.
"""

import time
from typing import Optional
import asyncio
import logging

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base_ai_service import BaseAIService, AIAnswerSuggestion, AIServiceError
from PIL import Image

class GeminiAnswerService(BaseAIService):
    """Google Gemini service for iClicker answer suggestions.

    Uses Google's Gemini model to analyze question screenshots
    and provide intelligent answer suggestions with reasoning.

    Attributes:
        model (GenerativeModel): Gemini model instance
    """

    SUPPORTED_MODELS = [
        "gemini-pro-vision",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest"
    ]

    DEFAULT_MODEL = "gemini-1.5-flash-latest"

    def __init__(self, api_key: str, model_name: Optional[str] = None) -> None:
        """Initialize the Gemini service.

        Args:
            api_key: Google API key for Gemini
            model_name: Specific Gemini model to use

        Raises:
            AIServiceError: If Gemini is not available or initialization fails
        """
        if not GEMINI_AVAILABLE:
            raise AIServiceError(
                "Google Generative AI package not installed. Install with: pip install google-generativeai"
            )

        model_name = model_name or self.DEFAULT_MODEL
        super().__init__(api_key, model_name)

        if model_name not in self.SUPPORTED_MODELS:
            self.logger.warning(f"Model {model_name} not in supported list. Proceeding anyway.")

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            raise AIServiceError(f"Failed to initialize Gemini client: {e}") from e

    async def analyze_question(self, image_path: str, question_text: str = "") -> AIAnswerSuggestion:
        """Analyze a question image using Gemini.

        Args:
            image_path: Path to the question screenshot
            question_text: Optional extracted text from the question

        Returns:
            AIAnswerSuggestion with Gemini's recommended answer

        Raises:
            AIServiceError: If analysis fails
        """
        start_time = time.time()

        try:
            img = Image.open(image_path)
            prompt = self._create_analysis_prompt(question_text)

            response = await self.model.generate_content_async([prompt, img])

            suggestion = self._parse_response(response, time.time() - start_time)

            self.logger.info(f"Gemini analysis completed: {suggestion.suggested_answer} ({suggestion.confidence_percentage})")
            return suggestion

        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            raise AIServiceError(f"Failed to analyze question with Gemini: {e}") from e

    def test_connection(self) -> bool:
        """Test the connection to Gemini API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # A simple way to test connection is to list models
            models = genai.list_models()
            return any(self.model_name in m.name for m in models)
        except Exception as e:
            self.logger.error(f"Gemini connection test failed: {e}")
            return False

    @property
    def service_name(self) -> str:
        """Get the name of this AI service."""
        return "Google Gemini"

    @property
    def supported_models(self) -> list:
        """Get list of supported Gemini models."""
        return self.SUPPORTED_MODELS.copy()

    def _create_analysis_prompt(self, question_text: str = "") -> str:
        """Create the analysis prompt for Gemini.

        Args:
            question_text: Optional extracted text from the question

        Returns:
            Formatted prompt string
        """
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
        """Parse Gemini response into AIAnswerSuggestion.

        Args:
            response: Raw response from Gemini
            processing_time: Time taken for processing

        Returns:
            Parsed AIAnswerSuggestion

        Raises:
            AIServiceError: If response parsing fails
        """
        try:
            import json
            response_text = response.text.strip()

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
            self.logger.error(f"Failed to parse Gemini response: {e}")
            return AIAnswerSuggestion(
                suggested_answer="C",
                confidence=0.1,
                reasoning=f"Failed to parse AI response. Error: {str(e)}",
                model_used=self.model_name,
                processing_time=processing_time
            )

def create_gemini_service(api_key: Optional[str], model_name: Optional[str] = None) -> Optional[GeminiAnswerService]:
    """Factory function to create a Gemini service.

    Args:
        api_key: Google API key (can be None to disable AI)
        model_name: Specific model to use (optional)

    Returns:
        GeminiAnswerService instance if key provided, None otherwise
    """
    if not api_key:
        return None

    try:
        return GeminiAnswerService(api_key, model_name)
    except AIServiceError as e:
        logging.error(f"Failed to create Gemini service: {e}")
        return None