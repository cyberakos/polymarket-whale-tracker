"""Streamlit Web Dashboard a Polymarket Whale Tracking rendszerhez."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from analytics import ConsensusAnalyzer
from client import PolymarketClient
from config import settings
from models import ConsensusMarket


def init_page_config() -> None:
    st.set_page_config(
        page_title="Polymarket Whale Consensus Radar",
        page_icon="🐋",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        .metric-card {
            background-color: #131722;
            border: 1px solid #2a2e39;
            border-radius: 8px;
            padding: 16px;
            color: #d1d4dc;
        }
        .consensus-pill-high {
            background-color: #0e3d2f;
            color: #00f2a1;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }
        .consensus-pill-low {
            background-color: #3d141e;
            color: #ff4d6d;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    st.sidebar.title("🐋 Vezérlőpult")
    st.sidebar.markdown("---")

    st.sidebar.subheader("⚙️ Kvantitatív Paraméterek")
    
    # ITT ÁLLÍTHATOD A BÁLNÁK SZÁMÁT KÖZVETLENÜL:
    whale_limit = st.sidebar.select_slider(
        "Vizsgált Top Bálnák Száma",
        options=[25, 50, 100, 150, 200],
        value=100,
        help="Hány bálnát olvasson be a Polymarket ranglistájáról",
    )

    user_bankroll = st.sidebar.number_input(
        "Kereskedési Tőke (USD)",
        min_value=10.0,                     # Engedélyezzük a kisebb összegeket is (pl. $50)
        max_value=10_000_000.0,
        value=max(10.0, float(getattr(settings, "DEFAULT_BANKROLL_USD", 1000.0))),
        step=50.0,
        key="user_bankroll_input",          # Az egyedi kulcs azonnal törli a hibásan beragadt értéket
    )

    kelly_profile = st.sidebar.select_slider(
        "Kelly Kockázati Profil",
        options=[0.25, 0.33, 0.50, 0.75, 1.0],
        value=settings.DEFAULT_KELLY_FRACTION,
        format_func=lambda x: f"{x}x (Fél-Kelly)" if x == 0.5 else f"{x}x Kelly",
    )

    min_whales = st.sidebar.slider(
        "Minimális Bálna Egyezés (fő)",
        min_value=2,
        max_value=15,
        value=3,
    )

    min_consensus_pct = st.sidebar.slider(
        "Minimális Konszenzus Arány (%)",
        min_value=50,
        max_value=100,
        value=75,
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌐 Hálózat")
    proxy_input = st.sidebar.text_input(
        "HTTP/SOCKS5 Proxy URL",
        value=settings.DEFAULT_PROXY or "",
        placeholder="http://127.0.0.1:7890",
    )
    force_mock = st.sidebar.checkbox("Kizárólag Szintetikus Adatok", value=False)

    refresh_interval_sec = st.sidebar.selectbox(
        "Automatikus Frissítés",
        options=[0, 30, 60, 120, 300],
        index=2,
        format_func=lambda x: "Kikapcsolva" if x == 0 else f"{x} másodperc",
    )

    return (
        whale_limit,
        min_whales,
        float(min_consensus_pct),
        user_bankroll,
        kelly_profile,
        proxy_input,
        force_mock,
        refresh_interval_sec,
    )


@st.cache_data(ttl=60)
def load_whale_data(whale_limit: int, proxy: str, mock_only: bool) -> tuple[list, list]:
    client = PolymarketClient(proxy_url=proxy if proxy.strip() else None)
    if mock_only:
        traders = client._generate_mock_traders(count=whale_limit)
    else:
        traders = client.fetch_top_traders(total_limit=whale_limit)
    positions = client.fetch_active_positions(traders)
    return traders, positions


def main() -> None:
    init_page_config()
    inject_custom_css()

    (
        whale_limit,
        min_whales,
        min_consensus_pct,
        bankroll,
        kelly_fraction,
        proxy_url,
        force_mock,
        refresh_sec,
    ) = render_sidebar()

    # Automatikus frissítés beállítása
    if refresh_sec > 0:
        st_autorefresh(interval=refresh_sec * 1000, key="datarefresh")

    st.title("🎯 Polymarket Whale Consensus & Alpha Radar")
    st.caption("Valós idejű intézményi méretű fogadások, konszenzus-detektálás és optimális pozícióméretezés.")

    # Adatletöltés
    with st.spinner(f"{whale_limit} bálna és nyitott pozícióik szinkronizálása..."):
        traders, positions = load_whale_data(whale_limit, proxy_url, force_mock)

    # Elemző modul futtatása
    analyzer = ConsensusAnalyzer(
        min_whales_consensus=min_whales,
        min_consensus_pct=min_consensus_pct,
        bankroll_usd=bankroll,
        kelly_fraction=kelly_fraction,
    )
    all_consensus = analyzer.analyze_positions(positions)

    # Szűrés a felhasználói limitek alapján
    filtered_markets = [
        m
        for m in all_consensus
        if m.whale_count_dominant >= min_whales
        and (m.consensus_ratio * 100.0) >= min_consensus_pct
    ]

    # Felső KPI blokk
    col1, col2, col3, col4 = st.columns(4)
    total_whale_capital = sum(p.size_usd for p in positions)
    avg_top_pnl = sum(t.pnl_usd for t in traders[:20]) / 20.0

    col1.metric("Figyelt Top Bálnák", f"{len(traders)} tárca")
    col2.metric("Összes Bálna Kitettség", f"${total_whale_capital:,.0f}")
    col3.metric("Kiemelt Alpha Piacok", f"{len(filtered_markets)} db")
    col4.metric("Top 20 Bálna Átl. PnL", f"${avg_top_pnl:,.0f}")

    st.markdown("---")

    # Két paneles elrendezés: Táblázat és Vizualizáció
    tab_overview, tab_distribution = st.tabs(["📋 Konszenzus Táblázat", "📊 Tőkeeloszlási Grafikonok"])

    with tab_overview:
        if not filtered_markets:
            st.warning("A megadott szűrési feltételeknek (min. bálna és konszenzus %) egyetlen piac sem felelt meg.")
        else:
            # app.py -> tab_overview blokkban:

            table_rows = []
            for m in filtered_markets:
                table_rows.append(
                    {
                        "Piac": m.market_title,
                        "Kimenetel": m.dominant_outcome,
                        "Bálna Egyezés": f"{m.whale_count_dominant} / {m.total_whales}",
                        "Konszenzus %": f"{m.consensus_ratio * 100:.1f}%",
                        "Domináns Tőke": f"${m.dominant_capital_usd:,.0f}",
                        "VWAP Ár": f"${m.vwap_entry_price:.2f}",
                        "Piaci Ár": f"${m.current_market_price:.2f}",
                        "Bálna WinRate": f"{m.avg_whale_win_rate * 100:.1f}%",
                        "Opportunity Score": m.opportunity_score,
                        "Ajánlott Akció": m.recommended_action,
                        "Javasolt Tét (USD)": f"${m.suggested_size_usd:,.0f}",
                        "Polymarket": m.market_url,  # <-- UTOLSÓ OSZLOP
                    }
                )
            df = pd.DataFrame(table_rows)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Opportunity Score": st.column_config.ProgressColumn(
                        "Opportunity Score",
                        help="Kvantitatív pontszám a konszenzus ereje és kockázata alapján",
                        format="%f",
                        min_value=0,
                        max_value=100,
                    ),
                    "Polymarket": st.column_config.LinkColumn(  # <-- KATTINTHATÓ LINK BEÁLLÍTÁSA
                        "Polymarket Piac",
                        display_text="Megnyitás ↗",
                        help="Kattints a piac közvetlen megnyitásához új lapon",
                    ),
                },
            )

    with tab_distribution:
        if filtered_markets:
            chart_data = pd.DataFrame(
                [
                    {
                        "Market": m.market_title[:35] + "...",
                        "Whale Capital (USD)": m.dominant_capital_usd,
                        "Consensus %": m.consensus_ratio * 100,
                        "Score": m.opportunity_score,
                    }
                    for m in filtered_markets
                ]
            )
            fig = px.scatter(
                chart_data,
                x="Consensus %",
                y="Whale Capital (USD)",
                size="Score",
                color="Score",
                hover_name="Market",
                color_continuous_scale="Viridis",
                title="Bálna Tőke vs. Konszenzus Erőssége (Buborékméret = Opportunity Score)",
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    # Részletes tárcavizsgáló (Drill-Down)
    st.markdown("---")
    st.subheader("🔍 Piac és Tárca Részletező (Deep-Dive)")

    if filtered_markets:
        market_options = {m.market_title: m for m in filtered_markets}
        selected_title = st.selectbox("Válassz egy piacot a tárcák ellenőrzéséhez:", options=list(market_options.keys()))

        selected_market: ConsensusMarket = market_options[selected_title]

        det_c1, det_c2, det_c3 = st.columns([1, 1, 2])
        det_c1.metric("Domináns Kimenetel", selected_market.dominant_outcome)
        det_c2.metric("Ajánlott Pozícióméret", f"${selected_market.suggested_size_usd:,.0f}")
        det_c3.info(
            f"**Kvantitatív összefoglaló:** {selected_market.whale_count_dominant} bálna áll a(z) "
            f"**{selected_market.dominant_outcome}** oldalon..."
            f"**${selected_market.dominant_capital_usd:,.0f}** tőkével, míg az ellenkező oldalon "
            f"{selected_market.whale_count_opposing} bálna fogadott (${selected_market.opposing_capital_usd:,.0f})."
        )

        st.write("#### A piacban résztvevő bálnák listája:")
        wallet_rows = []
        for c in selected_market.contributions:
            wallet_rows.append(
                {
                    "Tárca Neve": c.wallet_name,
                    "Cím": c.wallet_address,
                    "Kimenetel": c.outcome,
                    "Befektetett Összeg": f"${c.size_usd:,.2f}",
                    "Belépési Ár": f"${c.avg_price:.2f}",
                    "Becsült Win Rate": f"{c.win_rate * 100:.1f}%",
                }
            )
        wallet_df = pd.DataFrame(wallet_rows)
        st.dataframe(wallet_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()