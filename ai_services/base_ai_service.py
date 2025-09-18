"""Base AI service interface for iClicker answer suggestions.

This module defines the abstract base class for AI services that
provide answer suggestions based on question screenshots.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging


class AIServiceError(Exception):
    """Exception raised when AI service operations fail."""
    pass


@dataclass
class AIAnswerSuggestion:
    """Container for AI-generated answer suggestions.

    Attributes:
        suggested_answer (str): The AI's suggested answer choice (A, B, C, D, E)
        confidence (float): Confidence score from 0.0 to 1.0
        reasoning (str): AI's explanation for the suggested answer
        model_used (str): Name/version of the AI model used
        processing_time (float): Time taken to generate the suggestion in seconds
    """
    suggested_answer: str
    confidence: float
    reasoning: str
    model_used: str
    processing_time: float

    def __post_init__(self) -> None:
        """Validate the answer suggestion after initialization."""
        valid_answers = ['A', 'B', 'C', 'D', 'E']
        if self.suggested_answer not in valid_answers:
            raise ValueError(f"Invalid answer: {self.suggested_answer}. Must be one of {valid_answers}")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def confidence_percentage(self) -> str:
        """Get confidence as a formatted percentage string."""
        return f"{self.confidence * 100:.1f}%"

    def __str__(self) -> str:
        """Return a human-readable representation of the suggestion."""
        return (f"Answer: {self.suggested_answer} "
                f"(Confidence: {self.confidence_percentage}) - {self.reasoning}")


class BaseAIService(ABC):
    """Abstract base class for AI answer suggestion services.

    This class defines the interface that all AI services must implement
    to provide answer suggestions for iClicker questions.
    """

    def __init__(self, api_key: str, model_name: str = "default") -> None:
        """Initialize the AI service.

        Args:
            api_key: API key for the AI service
            model_name: Name of the specific model to use

        Raises:
            AIServiceError: If initialization fails
        """
        if not api_key:
            raise AIServiceError("API key is required")

        self.api_key = api_key
        self.model_name = model_name
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def analyze_question(self, image_path: str, question_text: str = "") -> AIAnswerSuggestion:
        """Analyze a question image and provide an answer suggestion.

        Args:
            image_path: Path to the question screenshot
            question_text: Optional extracted text from the question

        Returns:
            AIAnswerSuggestion with the AI's recommended answer

        Raises:
            AIServiceError: If analysis fails
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the AI service.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Get the name of this AI service."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list:
        """Get list of supported model names."""
        pass