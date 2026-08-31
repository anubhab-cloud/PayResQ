"""
app/agents/providers/base.py
=============================
Abstract base class for all LLM providers.

Each provider must implement generate_decision() which accepts a
prompt string and returns a raw string response from the LLM.
The caller is responsible for parsing and validating the response.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def generate_decision(self, prompt: str) -> str:
        """
        Send the prompt to the LLM and return the raw text response.

        Raises:
            LLMProviderError: If the provider is unavailable or times out.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""


class LLMProviderError(Exception):
    """Raised when the LLM provider cannot generate a response."""
