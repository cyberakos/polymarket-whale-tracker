"""Konszenzus- és kvantitatív motor dinamikus kimenetel-kezeléssel."""

from __future__ import annotations

from collections import defaultdict
import urllib.parse
import numpy as np

from config import settings
from models import ConsensusMarket, Position, WhaleContribution


class ConsensusAnalyzer:
    def __init__(
        self,
        min_whales_consensus: int = 3,
        min_consensus_pct: float = 75.0,
        bankroll_usd: float = 25000.0,
        kelly_fraction: float = 0.5,
    ):
        self.min_whales = min_whales_consensus
        self.min_consensus_pct = min_consensus_pct
        self.bankroll = bankroll_usd
        self.kelly_fraction = kelly_fraction

    def analyze_positions(self, positions: list[Position]) -> list[ConsensusMarket]:
        markets_map: dict[str, list[Position]] = defaultdict(list)
        for pos in positions:
            markets_map[pos.market_title].append(pos)

        consensus_list: list[ConsensusMarket] = []

        for title, pos_list in markets_map.items():
            # Csoportosítás a valódi kimenetel nevek szerint (pl. "Orioles" vs "Yankees")
            outcomes_capital: dict[str, float] = defaultdict(float)
            outcomes_positions: dict[str, list[Position]] = defaultdict(list)

            for p in pos_list:
                outcomes_capital[p.outcome] += p.size_usd
                outcomes_positions[p.outcome].append(p)

            total_cap = sum(outcomes_capital.values())
            if total_cap <= 0:
                continue

            # Megkeressük a legtöbb tőkét vonzó domináns kimenetelt
            dominant_outcome = max(outcomes_capital, key=outcomes_capital.get)
            dominant_positions = outcomes_positions[dominant_outcome]
            dominant_cap = outcomes_capital[dominant_outcome]
            opposing_cap = total_cap - dominant_cap

            whales_dominant = len(dominant_positions)
            total_whales = len(pos_list)
            whales_opposing = total_whales - whales_dominant

            consensus_ratio = dominant_cap / total_cap

            # VWAP és átlagos piaci ár a domináns kimenetelre
            vwap = sum(p.avg_price * p.size_usd for p in dominant_positions) / dominant_cap
            cur_price = float(np.mean([p.current_price for p in dominant_positions]))
            avg_win_rate = float(np.mean([p.wallet_win_rate for p in dominant_positions]))

            opp_score = self._calculate_opportunity_score(
                consensus_ratio=consensus_ratio,
                whales_count=whales_dominant,
                avg_win_rate=avg_win_rate,
                total_capital_usd=dominant_cap,
                cur_price=cur_price,
            )

            action, suggested_wager = self._calculate_position_size(
                cur_price=cur_price,
                estimated_win_prob=avg_win_rate,
                consensus_ratio=consensus_ratio,
                opp_score=opp_score,
            )

            slug = next((p.market_slug for p in pos_list if p.market_slug), None)
            if slug:
                market_url = f"https://polymarket.com/event/{slug}"
            else:
                market_url = f"https://polymarket.com/events?q={urllib.parse.quote_plus(title)}"

            contributions = [
                WhaleContribution(
                    wallet_address=p.wallet_address,
                    wallet_name=p.wallet_name,
                    win_rate=p.wallet_win_rate,
                    outcome=p.outcome,
                    size_usd=p.size_usd,
                    avg_price=p.avg_price,
                )
                for p in pos_list
            ]

            consensus_list.append(
                ConsensusMarket(
                    market_id=pos_list[0].market_id,
                    market_title=title,
                    market_slug=slug,
                    market_url=market_url,
                    dominant_outcome=dominant_outcome,
                    whale_count_dominant=whales_dominant,
                    whale_count_opposing=whales_opposing,
                    total_whales=total_whales,
                    dominant_capital_usd=dominant_cap,
                    opposing_capital_usd=opposing_cap,
                    total_capital_usd=total_cap,
                    consensus_ratio=round(consensus_ratio, 4),
                    vwap_entry_price=round(vwap, 3),
                    current_market_price=round(cur_price, 3),
                    avg_whale_win_rate=round(avg_win_rate, 3),
                    opportunity_score=round(opp_score, 1),
                    recommended_action=action,
                    suggested_size_usd=round(suggested_wager, 2),
                    kelly_fraction_used=self.kelly_fraction,
                    contributions=contributions,
                )
            )

        consensus_list.sort(key=lambda x: x.opportunity_score, reverse=True)
        return consensus_list

    def _calculate_opportunity_score(
        self,
        consensus_ratio: float,
        whales_count: int,
        avg_win_rate: float,
        total_capital_usd: float,
        cur_price: float,
    ) -> float:
        c_score = max(0.0, (consensus_ratio - 0.50) / 0.50) * 35.0
        w_score = min(1.0, whales_count / 8.0) * 25.0
        wr_score = max(0.0, (avg_win_rate - 0.50) / 0.35) * 20.0
        cap_score = min(1.0, np.log10(max(10_000.0, total_capital_usd)) / 6.0) * 15.0
        price_edge = max(0.0, (1.0 - cur_price)) * 5.0
        return float(np.clip(c_score + w_score + wr_score + cap_score + price_edge, 0.0, 100.0))

    def _calculate_position_size(
        self,
        cur_price: float,
        estimated_win_prob: float,
        consensus_ratio: float,
        opp_score: float,
    ) -> tuple[str, float]:
        if cur_price <= 0.02 or cur_price >= 0.98 or opp_score < 50.0:
            return "HOLD / SKIP", 0.0
        adjusted_p = (estimated_win_prob * 0.6) + (consensus_ratio * 0.4)
        c = cur_price
        if adjusted_p <= c:
            return "NEUTRAL / NO EDGE", 0.0
        raw_kelly = (adjusted_p - c) / (1.0 - c)
        fractional_kelly = raw_kelly * self.kelly_fraction
        clamped_kelly = max(0.0, min(settings.MAX_POSITION_PCT_CAP, fractional_kelly))
        recommended_usd = clamped_kelly * self.bankroll
        action = "STRONG BUY" if opp_score >= 75.0 and recommended_usd > 0 else "ACCUMULATE"
        return action, recommended_usd