"""Monitoring services for iClicker Evade.

This package provides monitoring functionality for iClicker sessions,
including question detection, screenshot capture, and user interaction.
"""

from .question_monitor import QuestionMonitor

__all__ = ['QuestionMonitor']