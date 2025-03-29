"""
Experimentation Platform package initialization.

This module initializes the experimentation platform package
and imports core components for easy access.
"""

# Import version information
__version__ = "1.0.0"

# Import core components (avoid circular imports)
# Do NOT import settings here - that creates a circular import
# The settings should be imported directly from the config module when needed
# from backend.app.core.config import settings
