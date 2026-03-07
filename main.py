#!/usr/bin/env python3
"""Automated Bots — Algorithmic market signal generation (simulated)."""
import json, os, random, math, datetime, hashlib

TICKERS = ["BTC", "ETH", "SOL", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "GOOG", "META"]

def generate_ohlcv(ticker, base_price=None):
    if base_price is None:
        base_price = random.uniform(10, 5000)
    volatility = random.uniform(0.01, 0.08)
    open_p = base_price * (1 + random.gauss(0, volatility))
    high_p = open_p * (1 + abs(random.gauss(0, volatility)))
    low_p = open_p * (1 - abs(random.gauss(0, volatility)))
    close_p = random.uniform(low_p, high_p)
    volume = int(random.uniform(1e5, 1e8))
    return {
        "ticker": ticker,
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "close": round(close_p, 2),
        "volume": volume,
    }

def compute_indicators(candles):
    closes = [c["close"] for c in candles]
    sma_5 = sum(closes[-5:]) / min(len(closes), 5)
    sma_20 = sum(closes) / len(closes)
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    volatility = (sum(r**2 for r in returns) / max(len(returns), 1)) ** 0.5 if returns else 0

    gains = [r for r in returns if r > 0]
    losses = [-r for r in returns if r < 0]
    avg_gain = sum(gains) / max(len(gains), 1)
    avg_loss = sum(losses) / max(len(losses), 1)
    rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 50

    momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0

    return {
        "sma_5": round(sma_5, 2),
        "sma_20": round(sma_20, 2),
        "rsi": round(rsi, 2),
        "volatility": round(volatility, 6),
        "momentum": round(momentum, 4),
    }

def generate_signal(indicators, candle):
    score = 0
    reasons = []

    if indicators["sma_5"] > indicators["sma_20"]:
        score += 1
        reasons.append("SMA5 > SMA20 (bullish cross)")
    else:
        score -= 1
        reasons.append("SMA5 < SMA20 (bearish cross)")

    if indicators["rsi"] < 30:
        score += 2
        reasons.append(f"RSI oversold ({indicators['rsi']})")
    elif indicators["rsi"] > 70:
        score -= 2
        reasons.append(f"RSI overbought ({indicators['rsi']})")

    if indicators["momentum"] > 0.02:
        score += 1
        reasons.append(f"Positive momentum ({indicators['momentum']})")
    elif indicators["momentum"] < -0.02:
        score -= 1
        reasons.append(f"Negative momentum ({indicators['momentum']})")

    if score >= 2:
        signal = "STRONG_BUY"
    elif score == 1:
        signal = "BUY"
    elif score == 0:
        signal = "HOLD"
    elif score == -1:
        signal = "SELL"
    else:
        signal = "STRONG_SELL"

    return {"signal": signal, "score": score, "reasons": reasons, "confidence": round(min(abs(score) / 4, 1.0), 2)}

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    all_signals = []
    for ticker in TICKERS:
        base = random.uniform(10, 5000)
        candles = [generate_ohlcv(ticker, base * (1 + random.gauss(0, 0.02))) for _ in range(20)]
        indicators = compute_indicators(candles)
        signal = generate_signal(indicators, candles[-1])
        all_signals.append({
            "ticker": ticker,
            "latest_price": candles[-1]["close"],
            "indicators": indicators,
            "signal": signal,
        })

    all_signals.sort(key=lambda x: x["signal"]["score"], reverse=True)

    report = {
        "timestamp": now.isoformat(),
        "run_id": hashlib.sha256(now.isoformat().encode()).hexdigest()[:10],
        "market_summary": {
            "tickers_scanned": len(TICKERS),
            "buy_signals": sum(1 for s in all_signals if "BUY" in s["signal"]["signal"]),
            "sell_signals": sum(1 for s in all_signals if "SELL" in s["signal"]["signal"]),
            "hold_signals": sum(1 for s in all_signals if s["signal"]["signal"] == "HOLD"),
        },
        "signals": all_signals,
    }

    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{date_str}.json", "w") as f:
        json.dump(report, f, indent=2)

    md = [f"# Market Signal Report — {date_str}\n"]
    md.append(f"**Run ID:** `{report['run_id']}`\n")
    md.append(f"## Market Summary\n")
    ms = report["market_summary"]
    md.append(f"| Metric | Value |")
    md.append(f"|--------|-------|")
    md.append(f"| Tickers Scanned | {ms['tickers_scanned']} |")
    md.append(f"| Buy Signals | {ms['buy_signals']} |")
    md.append(f"| Sell Signals | {ms['sell_signals']} |")
    md.append(f"| Hold Signals | {ms['hold_signals']} |")
    md.append(f"\n## Signal Dashboard\n")
    md.append(f"| Ticker | Price | Signal | Score | RSI | Momentum | Confidence |")
    md.append(f"|--------|-------|--------|-------|-----|----------|------------|")
    for s in all_signals:
        md.append(f"| {s['ticker']} | ${s['latest_price']} | **{s['signal']['signal']}** | {s['signal']['score']} | {s['indicators']['rsi']} | {s['indicators']['momentum']} | {s['signal']['confidence']} |")
    md.append(f"\n## Signal Details\n")
    for s in all_signals:
        if s["signal"]["signal"] in ("STRONG_BUY", "STRONG_SELL"):
            md.append(f"### {s['ticker']} — {s['signal']['signal']}")
            for r in s["signal"]["reasons"]:
                md.append(f"- {r}")
            md.append("")

    with open(f"logs/{date_str}.md", "w") as f:
        f.write("\n".join(md))

    print(f"[automated-bots] Report generated: logs/{date_str}.md")

if __name__ == "__main__":
    main()
