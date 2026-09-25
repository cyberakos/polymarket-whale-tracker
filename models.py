"""Adatmodellek dinamikus kimenetel-támogatással (pl. Csapatnevek, YES/NO)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# Visszatesszük a típust a meglévő importok kiszolgálására:
class OutcomeType(str, Enum):
    YES = "YES"
    NO = "NO"


class Trader(BaseModel):
    address: str
    username: str | None = None
    rank: int
    pnl_usd: float = 0.0
    volume_usd: float = 0.0
    estimated_win_rate: float = Field(default=0.60, ge=0.0, le=1.0)


class Position(BaseModel):
    wallet_address: str
    wallet_name: str
    wallet_win_rate: float
    market_id: str
    market_title: str
    market_slug: str | None = None
    outcome: str  # Elfogad bármilyen szöveget (pl. "New York Yankees", "YES", "NO")
    size_usd: float
    avg_price: float = Field(ge=0.01, le=0.99)
    current_price: float = Field(ge=0.01, le=0.99)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WhaleContribution(BaseModel):
    wallet_address: str
    wallet_name: str
    win_rate: float
    outcome: str
    size_usd: float
    avg_price: float


class ConsensusMarket(BaseModel):
    market_id: str
    market_title: str
    market_slug: str | None = None
    market_url: str
    dominant_outcome: str  # A győztes kimenetel neve (pl. "New York Yankees")
    whale_count_dominant: int
    whale_count_opposing: int
    total_whales: int
    dominant_capital_usd: float
    opposing_capital_usd: float
    total_capital_usd: float
    consensus_ratio: float
    vwap_entry_price: float
    current_market_price: float
    avg_whale_win_rate: float
    opportunity_score: float
    recommended_action: str
    suggested_size_usd: float
    kelly_fraction_used: float
    contributions: list[WhaleContribution]