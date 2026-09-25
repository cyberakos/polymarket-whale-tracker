"""Polymarket Kliens – Lapozott Leaderboard és Párhuzamosított Pozíciólekérés."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import Any
import httpx

from config import settings
from models import Position, Trader

logger = logging.getLogger(__name__)


class PolymarketClient:
    def __init__(self, proxy_url: str | None = None):
        self.proxy_url = proxy_url or settings.DEFAULT_PROXY
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

    def _get_client(self) -> httpx.Client:
        kwargs: dict[str, Any] = {
            "timeout": settings.REQUEST_TIMEOUT_SECONDS,
            "headers": self.headers,
            "follow_redirects": True,
        }
        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url
        return httpx.Client(**kwargs)

    def fetch_top_traders(self, total_limit: int = 100) -> list[Trader]:
        """Bálnák lekérése lapozással (50-es lapméret offsettel)."""
        all_traders: list[Trader] = []
        page_size = 50
        max_pages = (total_limit + page_size - 1) // page_size

        try:
            with self._get_client() as client:
                for page in range(max_pages):
                    offset = page * page_size
                    url = f"{settings.DATA_API_BASE}/v1/leaderboard"
                    params = {
                        "category": "OVERALL",
                        "timePeriod": "ALL",
                        "orderBy": "PNL",
                        "limit": page_size,
                        "offset": offset,
                    }
                    resp = client.get(url, params=params)
                    if resp.status_code != 200:
                        break

                    raw = resp.json()
                    items = raw if isinstance(raw, list) else raw.get("data", [])
                    if not items:
                        break

                    for idx, item in enumerate(items, start=len(all_traders) + 1):
                        address = item.get("proxyWallet") or item.get("user") or item.get("address")
                        if not address:
                            continue
                        all_traders.append(
                            Trader(
                                address=address,
                                username=item.get("userName") or item.get("pseudonym") or f"Whale_{idx}",
                                rank=idx,
                                pnl_usd=float(item.get("pnl", 0.0)),
                                volume_usd=float(item.get("vol") or item.get("volume", 0.0)),
                                estimated_win_rate=min(0.88, max(0.55, 0.70 + (0.005 * (20 - min(idx, 20))))),
                            )
                        )
                        if len(all_traders) >= total_limit:
                            break

            if all_traders:
                return all_traders
        except Exception as e:
            print(f"[Leaderboard Error]: {e}")

        return self._generate_mock_traders(count=total_limit)

    def _fetch_single_wallet(self, client: httpx.Client, trader: Trader) -> list[Position]:
        """Egyetlen tárca pozícióinak lekérése a háttérszálban."""
        wallet_positions: list[Position] = []
        try:
            url = f"{settings.DATA_API_BASE}/positions"
            params = {
                "user": trader.address,
                "sizeThreshold": "50",
                "limit": "100",
                "sortBy": "CURRENT",
            }
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                raw = resp.json()
                items = raw if isinstance(raw, list) else raw.get("data", [])
                for p in items:
                    if p.get("closed") is True or p.get("resolved") is True:
                        continue

                    cur_p = float(p.get("curPrice") or 0.0)
                    avg_p = float(p.get("avgPrice") or 0.50)
                    if cur_p <= 0.01 or cur_p >= 0.99:
                        continue

                    event_slug = p.get("eventSlug") or p.get("slug")
                    market_title = (p.get("title") or p.get("market", {}).get("question") or "").strip()
                    market_id = str(p.get("conditionId") or p.get("asset") or "").strip()
                    size = float(p.get("size") or p.get("curAmt") or p.get("currentValue") or 0.0)

                    if size >= 100 and market_id and market_title:
                        raw_outcome = p.get("outcome") or p.get("outcomeLabel") or "YES"
                        outcome = str(raw_outcome).strip()

                        wallet_positions.append(
                            Position(
                                wallet_address=trader.address,
                                wallet_name=trader.username or trader.address[:8],
                                wallet_win_rate=trader.estimated_win_rate,
                                market_id=market_id,
                                market_title=market_title,
                                market_slug=str(event_slug) if event_slug else None,
                                outcome=outcome,
                                size_usd=size,
                                avg_price=max(0.01, min(0.99, avg_p)),
                                current_price=max(0.01, min(0.99, cur_p)),
                            )
                        )
        except Exception:
            pass
        return wallet_positions

    def fetch_active_positions(self, traders: list[Trader]) -> list[Position]:
        """Az összes beolvasott bálna pozícióinak párhuzamos (gyors) lekérése."""
        all_positions: list[Position] = []

        # 10 szálon egyszerre küldjük ki a kéréseket, így 200 bálna is másodpercek alatt bejön
        with self._get_client() as client:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_trader = {
                    executor.submit(self._fetch_single_wallet, client, t): t
                    for t in traders
                }
                for future in as_completed(future_to_trader):
                    result = future.result()
                    if result:
                        all_positions.extend(result)

        return all_positions

    def _generate_mock_traders(self, count: int = 100) -> list[Trader]:
        import random
        random.seed(42)
        return [
            Trader(
                address=f"0x{random.randint(0x1000000000000000, 0xFFFFFFFFFFFFFFFF):016x}{i:024x}",
                username=f"Whale_{i:03d}",
                rank=i,
                pnl_usd=round(random.lognormvariate(12.5, 0.8), 2),
                volume_usd=round(random.lognormvariate(14.0, 0.7), 2),
                estimated_win_rate=round(random.uniform(0.58, 0.82), 3),
            )
            for i in range(1, count + 1)
        ]