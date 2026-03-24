"""
Configuration Manager Singleton.

Provides a single, shared configuration instance across the entire application.
Used for settings like DEFAULT_PAGE_SIZE, ENABLE_ANALYTICS, and RATE_LIMIT.

Usage:
    from singletons.config_manager import ConfigManager
    config = ConfigManager()
    page_size = config.get_setting('DEFAULT_PAGE_SIZE')
"""


class ConfigManager:
    """
    Singleton class for managing application configuration.
    
    Ensures only one instance exists throughout the application lifecycle.
    All views and modules share the same configuration state.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Create a new instance only if one doesn't exist."""
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize default configuration settings."""
        self.settings = {
            "DEFAULT_PAGE_SIZE": 20,      # Default posts per page in feed
            "ENABLE_ANALYTICS": True,     # Toggle analytics tracking
            "RATE_LIMIT": 100             # Max requests per minute
        }

    def get_setting(self, key):
        """Retrieve a configuration value by key."""
        return self.settings.get(key)

    def set_setting(self, key, value):
        """Update a configuration value."""
        self.settings[key] = value