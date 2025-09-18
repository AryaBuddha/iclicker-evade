"""Utility functions for iClicker Evade.

This package provides common utility functions used throughout
the application for browser management, validation, and helpers.
"""

from .browser_utils import setup_chrome_driver, safe_quit_driver
from .validators import validate_email_address

__all__ = ['setup_chrome_driver', 'safe_quit_driver', 'validate_email_address']