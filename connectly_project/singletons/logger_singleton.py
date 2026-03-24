"""
Logger Singleton.

Provides a single, shared logger instance for consistent logging
across the entire application.

Usage:
    from singletons.logger_singleton import LoggerSingleton
    logger = LoggerSingleton().get_logger()
    logger.info("Message here")
"""

import logging


class LoggerSingleton:
    """
    Singleton class for application-wide logging.
    
    Ensures all modules use the same logger instance with
    consistent formatting and configuration.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Create a new instance only if one doesn't exist."""
        if not cls._instance:
            cls._instance = super(LoggerSingleton, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the logger with console output and formatting."""
        self.logger = logging.getLogger("connectly_logger")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def get_logger(self):
        """Return the shared logger instance."""
        return self.logger