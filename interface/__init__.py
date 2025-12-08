"""
interface/__init__.py

UEM Interface Module - Kullanici arayuzleri.

Moduller:
- chat: CLI chat arayuzu
- api: REST API
- dashboard: Web dashboard
"""

from .chat import CLIChat

__all__ = ["CLIChat"]
