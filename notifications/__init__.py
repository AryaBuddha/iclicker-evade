"""Notification services for iClicker Evade.

This package provides notification services including email alerts
for question detection and other important events.
"""

from .email_service import EmailNotificationService

__all__ = ['EmailNotificationService']