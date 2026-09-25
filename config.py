"""Polymarket Whale Tracker konfigurációs modul."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Polymarket API végpontok
    DATA_API_BASE: str = "https://data-api.polymarket.com"
    GAMMA_API_BASE: str = "https://gamma-api.polymarket.com"

    # Hálózati beállítások
    REQUEST_TIMEOUT_SECONDS: float = 12.0
    MAX_RETRIES: int = 3
    DEFAULT_PROXY: str | None = Field(
        default_factory=lambda: os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    )

    # Alapértelmezett elemzési paraméterek
    DEFAULT_TOP_WHALES_COUNT: int = 100
    DEFAULT_MIN_WHALES_CONSENSUS: int = 3
    DEFAULT_MIN_CONSENSUS_PCT: float = 75.0
    DEFAULT_BANKROLL_USD: float = 50.0
    DEFAULT_KELLY_FRACTION: float = 0.5  # Fél-Kelly
    MAX_POSITION_PCT_CAP: float = 0.10  # Max tőke 10%-a egy pozícióra

    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )


settings = Settings()