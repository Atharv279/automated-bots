<div align="center">

# 📊 Automated Bots

[![Daily Signals](https://github.com/Atharv279/automated-bots/actions/workflows/daily_run.yml/badge.svg)](https://github.com/Atharv279/automated-bots/actions/workflows/daily_run.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Automated](https://img.shields.io/badge/Runs-Daily%20via%20CI-blue)

**Algorithmic market signal generator with technical analysis, visual dashboards, and day-over-day delta tracking.**

*Disclaimer: Simulated data only. Not financial advice.*

</div>

---

## Architecture

```mermaid
graph LR
    A[📈 OHLCV Generator] -->|20 Candles| B[📐 Technical Indicators]
    B -->|SMA, RSI, Momentum| C[🎯 Signal Engine]
    C -->|Score & Classify| D[📊 Dashboard Generator]
    C -->|Load Previous| E[🔄 Delta Engine]
    E -->|Signal Changes| F[📋 Report]
    D --> F
    F -->|Git Push| G[🚀 GitHub]
```

## Indicators

| Indicator | Method | Signal Logic |
|-----------|--------|-------------|
| **SMA Crossover** | SMA(5) vs SMA(20) | Bullish if SMA5 > SMA20 |
| **RSI** | 14-period relative strength | Oversold < 30, Overbought > 70 |
| **Momentum** | Price change over window | Positive > 2%, Negative < -2% |
| **Volatility** | Standard deviation of returns | Risk assessment |

## Live Dashboard Preview

![Dashboard](logs/2026-03-07_dashboard.png)

## Output Structure

```
logs/
├── YYYY-MM-DD.json          # Full signal data + indicators
├── YYYY-MM-DD.md            # Markdown report with delta
└── YYYY-MM-DD_dashboard.png # 4-panel visual dashboard
```

## Quick Start

```bash
pip install -r dev-requirements.txt
python main.py
```
