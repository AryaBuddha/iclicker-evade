"""OpenAI-based AI service for answer suggestions.

This module provides OpenAI GPT-4 Vision integration for analyzing
iClicker question screenshots and providing answer suggestions.
"""

import base64
import time
from typing import Optional
import asyncio
import logging

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base_ai_service import BaseAIService, AIAnswerSuggestion, AIServiceError


class OpenAIAnswerService(BaseAIService):
    """OpenAI GPT-4 Vision service for iClicker answer suggestions.

    Uses OpenAI's GPT-4 Vision model to analyze question screenshots
    and provide intelligent answer suggestions with reasoning.

    Attributes:
        client (OpenAI): OpenAI client instance
        model_name (str): GPT model to use (default: gpt-4-vision-preview)
        max_tokens (int): Maximum tokens for response
        temperature (float): Creativity setting (0.0-1.0)
    """

    # Default models and their capabilities
    SUPPORTED_MODELS = [
        "gpt-4-vision-preview",
        "gpt-4o",
        "gpt-4o-mini"
    ]

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model_name: Optional[str] = None) -> None:
        """Initialize the OpenAI service.

        Args:
            api_key: OpenAI API key
            model_name: Specific GPT model to use (defaults to gpt-4o)

        Raises:
            AIServiceError: If OpenAI is not available or initialization fails
        """
        if not OPENAI_AVAILABLE:
            raise AIServiceError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        model_name = model_name or self.DEFAULT_MODEL
        super().__init__(api_key, model_name)

        if model_name not in self.SUPPORTED_MODELS:
            self.logger.warning(f"Model {model_name} not in supported list. Proceeding anyway.")

        try:
            self.client = OpenAI(api_key=api_key)
            self.max_tokens = 500
            self.temperature = 0.1  # Low temperature for consistent answers
        except Exception as e:
            raise AIServiceError(f"Failed to initialize OpenAI client: {e}") from e

    async def analyze_question(self, image_path: str, question_text: str = "") -> AIAnswerSuggestion:
        """Analyze a question image using OpenAI GPT-4 Vision.

        Args:
            image_path: Path to the question screenshot
            question_text: Optional extracted text from the question

        Returns:
            AIAnswerSuggestion with GPT-4's recommended answer

        Raises:
            AIServiceError: If analysis fails
        """
        start_time = time.time()

        try:
            # Encode image to base64
            base64_image = self._encode_image(image_path)

            # Create the prompt
            prompt = self._create_analysis_prompt(question_text)

            # Make API call
            response = await self._call_openai_api(base64_image, prompt)

            # Parse response
            suggestion = self._parse_response(response, time.time() - start_time)

            self.logger.info(f"OpenAI analysis completed: {suggestion.suggested_answer} ({suggestion.confidence_percentage})")
            return suggestion

        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            raise AIServiceError(f"Failed to analyze question: {e}") from e

    def test_connection(self) -> bool:
        """Test the connection to OpenAI API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Make a simple API call to test connectivity
            response = self.client.chat.completions.create(
                model=self.model_name if self.model_name != "gpt-4-vision-preview" else "gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return bool(response.choices)
        except Exception as e:
            self.logger.error(f"OpenAI connection test failed: {e}")
            return False

    @property
    def service_name(self) -> str:
        """Get the name of this AI service."""
        return "OpenAI GPT-4 Vision"

    @property
    def supported_models(self) -> list:
        """Get list of supported OpenAI models."""
        return self.SUPPORTED_MODELS.copy()

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64 string.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded image string

        Raises:
            AIServiceError: If image encoding fails
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise AIServiceError(f"Failed to encode image {image_path}: {e}") from e

    def _create_analysis_prompt(self, question_text: str = "") -> str:
        """Create the analysis prompt for GPT-4 Vision.

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

    async def _call_openai_api(self, base64_image: str, prompt: str) -> dict:
        """Make the API call to OpenAI.

        Args:
            base64_image: Base64 encoded image
            prompt: Analysis prompt

        Returns:
            API response dictionary

        Raises:
            AIServiceError: If API call fails
        """
        try:
            # Run the blocking API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )

            if not response.choices:
                raise AIServiceError("No response from OpenAI API")

            return response.choices[0].message.content

        except Exception as e:
            raise AIServiceError(f"OpenAI API call failed: {e}") from e

    def _parse_response(self, response_content: str, processing_time: float) -> AIAnswerSuggestion:
        """Parse OpenAI response into AIAnswerSuggestion.

        Args:
            response_content: Raw response from OpenAI
            processing_time: Time taken for processing

        Returns:
            Parsed AIAnswerSuggestion

        Raises:
            AIServiceError: If response parsing fails
        """
        try:
            import json

            # Try to extract JSON from the response
            response_text = response_content.strip()

            # Handle cases where response might have extra text around JSON
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text

            data = json.loads(json_str)

            # Extract required fields
            answer = data.get("answer", "").upper()
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "No reasoning provided")

            # Validate answer format
            if answer not in ['A', 'B', 'C', 'D', 'E']:
                # Try to extract letter from response
                for char in response_text.upper():
                    if char in ['A', 'B', 'C', 'D', 'E']:
                        answer = char
                        reasoning = f"Extracted '{char}' from response: {reasoning}"
                        break
                else:
                    answer = "C"  # Default fallback
                    confidence = 0.1
                    reasoning = f"Could not parse answer from response. Defaulting to C. Original: {response_text[:100]}"

            return AIAnswerSuggestion(
                suggested_answer=answer,
                confidence=confidence,
                reasoning=reasoning,
                model_used=self.model_name,
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"Failed to parse OpenAI response: {e}")
            # Return a fallback suggestion
            return AIAnswerSuggestion(
                suggested_answer="C",
                confidence=0.1,
                reasoning=f"Failed to parse AI response. Error: {str(e)}",
                model_used=self.model_name,
                processing_time=processing_time
            )


def create_openai_service(api_key: Optional[str], model_name: Optional[str] = None) -> Optional[OpenAIAnswerService]:
    """Factory function to create an OpenAI service.

    Args:
        api_key: OpenAI API key (can be None to disable AI)
        model_name: Specific model to use (optional)

    Returns:
        OpenAIAnswerService instance if key provided, None otherwise
    """
    if not api_key:
        return None

    try:
        return OpenAIAnswerService(api_key, model_name)
    except AIServiceError as e:
        logging.error(f"Failed to create OpenAI service: {e}")
        return None