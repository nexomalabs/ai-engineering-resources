"""Shared helpers for Applied AI Engineering, Volume II laboratories.

Standard library only, so fixture playback works in a bare environment. The OpenAI
SDK is imported only when a lab records or calls the live API.
"""

from .fixtures import FixtureMissing, FixtureStore, lab_mode
from .openai_compat import OpenAI

__all__ = ["FixtureMissing", "FixtureStore", "OpenAI", "lab_mode"]
__version__ = "1.0.0"
