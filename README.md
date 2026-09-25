# 🐋 Polymarket Whale Consensus & Alpha Radar

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?style=for-the-badge)](https://github.com/cyberakos/polymarket-whale-tracker)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.7%2B-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![HTTPX](https://img.shields.io/badge/HTTPX-0.27%2B-10998E?style=for-the-badge)](https://www.python-httpx.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2%2B-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22%2B-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A production-grade, real-time decision-support system and analytics dashboard built on **Polymarket** prediction market data. It tracks smart money movements, extracts open positions of top-performing wallets (whales), clusters consensus outcomes, and computes optimal position sizing using a **Binary Fractional Kelly Criterion**.

---

## 📦 Stack & Core Dependencies

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Runtime** | Python | `>= 3.10` | Core application runtime |
| **Frontend Dashboard** | Streamlit | `>= 1.35.0` | Reactive web interface & metric cards |
| **Live UI Refresh** | streamlit-autorefresh | `>= 1.0.1` | Automatic interval-based polling |
| **Data Validation** | Pydantic | `>= 2.7.0` | Strict data typing and validation schemas |
| **Async / HTTP Client** | HTTPX (with SOCKS) | `>= 0.27.0` | High-throughput, proxy-aware HTTP requests |
| **Data Analytics** | Pandas / NumPy | `>= 2.2.0 / >= 1.26.0` | Position aggregation & weighted averages |
| **Visualization** | Plotly Express | `>= 5.22.0` | Interactive exposure & consensus scatter plots |

---

## ⚡ Key Features

- **Live Leaderboard Ingestion (Data API):** Fetches the top-performing traders directly from Polymarket's official `/v1/leaderboard` endpoint sorted by PnL and volume.
- **Concurrent Position Scanning (`ThreadPoolExecutor`):** Parallelized worker threads scan 50–200 whale wallets simultaneously in seconds without blocking the UI.
- **Dynamic Market & Outcome Parsing:** Supports both binary options (`YES` / `NO`) and multi-choice sports fixtures (extracting actual team names, spreads, and moneyline labels).
- **Consensus & Clustering Engine:**
  - Evaluates dominant vs. opposing capital and calculates the consensus ratio (`%`).
  - Computes Volume-Weighted Average Price (**VWAP**) and current market prices.
  - Aggregates historical win-rates of participating smart-money traders.
- **Quantitative Decision Engine:**
  - **Opportunity Score (0–100%):** Multi-factor scoring model combining consensus strength, whale count, volume concentration, and mispricing edge.
  - **Fractional Kelly Sizing:** Binary-option Kelly sizing engine configured with a configurable risk profile (e.g., Half-Kelly) and a strict 10% portfolio capital cap.
- **Interactive Web Dashboard:**
  - High-level KPI metrics (tracked whales, aggregate capital, top PnL).
  - Searchable, sortable consensus radar with **1-click direct link to live Polymarket events**.
  - **Deep-Dive Wallet Inspector:** Granular breakdown of individual wallet allocations, entry prices, and win rates for any selected market.
- **Fault-Tolerant Architecture:** Built-in proxy support (HTTP/SOCKS5) and synthetic mock generation fallback for zero-downtime offline testing.

---

## 📁 Repository Structure

```text
polymarket_whale_tracker/
├── config.py              # Central application settings, API URLs & safety caps
├── models.py              # Pydantic schemas (Trader, Position, ConsensusMarket)
├── client.py              # Parallelized Polymarket Data & Gamma API client
├── analytics.py           # Consensus clustering, Opportunity Score & Kelly engine
├── app.py                 # Streamlit web dashboard and visualization layer
├── test_connection.py     # Standalone diagnostic test script for network & API access
├── requirements.txt       # Pinned library dependencies
└── README.md              # Project documentation
```

---

## 📐 Mathematical Formulation

### 1. Opportunity Score (0 – 100)
The composite opportunity score aggregates five distinct quantitative dimensions:

1. **Consensus Dominance ($35\text{ pts}$):** Ratio of dominant capital relative to total whale capital in the market ($>50\%$).
2. **Whale Count Depth ($25\text{ pts}$):** Distinct smart money accounts on the dominant side (maxed out at $8+$ whales).
3. **Smart Money Quality ($20\text{ pts}$):** Average historical win-rate of the contributing whales.
4. **Capital Conviction ($15\text{ pts}$):** Logarithmically scaled USD capital commitment.
5. **Discount Edge ($5\text{ pts}$):** Pricing buffer based on entry level vs. terminal payout ($1 - c$).

$$\text{Score} = \text{clamp}\Big(S_{\text{consensus}} + S_{\text{count}} + S_{\text{quality}} + S_{\text{capital}} + S_{\text{price}},\, 0,\, 100\Big)$$

### 2. Binary Fractional Kelly Sizing
To determine the suggested wager from the user's available bankroll without risking ruin, the engine uses the binary contract Kelly formula:

$$f^* = \lambda \cdot \frac{p - c}{1 - c}$$

Where:
- $c \in (0, 1)$: Current market price (implied market probability).
- $p \in (0, 1)$: Adjusted win probability estimated from whale consensus and win rates.
- $\lambda$: Kelly fraction multiplier ($\lambda = 0.5$ for Half-Kelly).
- $\text{Safety Cap}$: The maximum capital allocated to any single opportunity is strictly capped at $10\%$ of total bankroll.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Network Note:** In regions where Polymarket domains are restricted at the ISP level (DPI/SNI filtering), active routing via **Cloudflare 1.1.1.1 with WARP** (free) or a standard VPN/Proxy is recommended.

### 2. Installation
```bash
# Clone the repository
git clone [https://github.com/cyberakos/polymarket-whale-tracker.git](https://github.com/cyberakos/polymarket-whale-tracker.git)
cd polymarket-whale-tracker

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Verify Live Connectivity
Run the diagnostic script to confirm clean connectivity to Polymarket's Gamma and Data APIs:
```bash
python test_connection.py
```
*A successful test returns HTTP 200 along with the #1 trader on the global leaderboard (e.g., Theo4).*

### 4. Launch the Dashboard
```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ⚙️ Dashboard Configuration (Sidebar)

- **Tracked Top Whales:** Adjustable slider (25 to 200 whales) determining how many top leaderboard accounts to audit.
- **Trading Bankroll (USD):** Total available portfolio capital used by the sizing algorithm.
- **Kelly Risk Profile:** Fraction of full Kelly applied (0.25x to 1.0x; default is 0.5x Half-Kelly).
- **Minimum Whale Consensus:** Threshold for the minimum number of matching whales required to highlight a market.
- **Minimum Consensus Ratio (%):** Minimum capital dominance percentage required (e.g., $75\%+$).
- **Auto-Refresh:** Configurable polling interval (30s, 60s, 120s, or Disabled).

---

## ⚠️ Disclaimer

This software is developed strictly for **educational, quantitative research, and decision-support purposes**. It does not constitute financial, investment, or gambling advice. Prediction markets carry substantial risk of capital loss. Always perform independent due diligence and exercise disciplined risk management before allocating real capital.
