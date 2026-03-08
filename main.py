#!/usr/bin/env python3
"""Automated Bots — Algorithmic market signal generation with visual analytics."""
import json
import os
import random
import datetime
import hashlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TICKERS = ["BTC", "ETH", "SOL", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "GOOG", "META"]
SIGNAL_COLORS = {"STRONG_BUY": "#27ae60", "BUY": "#2ecc71", "HOLD": "#f39c12", "SELL": "#e67e22", "STRONG_SELL": "#e74c3c"}

def generate_ohlcv(ticker, base_price=None):
    if base_price is None:
        base_price = random.uniform(10, 5000)
    v = random.uniform(0.01, 0.08)
    o = base_price * (1 + random.gauss(0, v))
    h = o * (1 + abs(random.gauss(0, v)))
    low = o * (1 - abs(random.gauss(0, v)))
    c = random.uniform(low, h)
    return {"ticker": ticker, "open": round(o,2), "high": round(h,2), "low": round(low,2), "close": round(c,2), "volume": int(random.uniform(1e5,1e8))}

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
    momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0
    return {"sma_5": round(sma_5,2), "sma_20": round(sma_20,2), "rsi": round(rsi,2), "volatility": round(volatility,6), "momentum": round(momentum,4)}

def generate_signal(indicators):
    score = 0
    reasons = []
    if indicators["sma_5"] > indicators["sma_20"]:
        score += 1
        reasons.append("SMA5 > SMA20 (bullish)")
    else:
        score -= 1
        reasons.append("SMA5 < SMA20 (bearish)")
    if indicators["rsi"] < 30:
        score += 2
        reasons.append(f"RSI oversold ({indicators['rsi']})")
    elif indicators["rsi"] > 70:
        score -= 2
        reasons.append(f"RSI overbought ({indicators['rsi']})")
    if indicators["momentum"] > 0.02:
        score += 1
        reasons.append(f"+momentum ({indicators['momentum']})")
    elif indicators["momentum"] < -0.02:
        score -= 1
        reasons.append(f"-momentum ({indicators['momentum']})")
    signals = {2: "STRONG_BUY", 1: "BUY", 0: "HOLD", -1: "SELL"}
    signal = signals.get(score, "STRONG_BUY" if score > 2 else "STRONG_SELL")
    return {"signal": signal, "score": score, "reasons": reasons, "confidence": round(min(abs(score)/4, 1.0), 2)}

def load_yesterday(date_str):
    yesterday = (datetime.datetime.strptime(date_str, "%Y-%m-%d") - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    path = f"logs/{yesterday}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def compute_delta(today_signals, yesterday_data):
    if not yesterday_data:
        return {"status": "no_previous_data"}
    y_map = {s["ticker"]: s for s in yesterday_data.get("signals", [])}
    deltas = {}
    for s in today_signals:
        y = y_map.get(s["ticker"])
        if y:
            price_change = round(((s["latest_price"] - y["latest_price"]) / y["latest_price"]) * 100, 2)
            deltas[s["ticker"]] = {"today_signal": s["signal"]["signal"], "yesterday_signal": y["signal"]["signal"],
                                    "price_change_pct": price_change, "signal_changed": s["signal"]["signal"] != y["signal"]["signal"]}
    return {"status": "compared", "deltas": deltas}

def generate_charts(all_signals, date_str):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f"Market Signal Dashboard — {date_str}", fontsize=14, fontweight="bold")

    # 1: Signal distribution
    signal_counts = {}
    for s in all_signals:
        sig = s["signal"]["signal"]
        signal_counts[sig] = signal_counts.get(sig, 0) + 1
    labels = list(signal_counts.keys())
    values = list(signal_counts.values())
    colors = [SIGNAL_COLORS.get(lbl, "#95a5a6") for lbl in labels]
    axes[0][0].pie(values, labels=labels, autopct="%1.0f%%", colors=colors, startangle=90)
    axes[0][0].set_title("Signal Distribution")

    # 2: RSI gauge
    tickers = [s["ticker"] for s in all_signals]
    rsis = [s["indicators"]["rsi"] for s in all_signals]
    rsi_colors = ["#e74c3c" if r > 70 else "#2ecc71" if r < 30 else "#3498db" for r in rsis]
    axes[0][1].barh(tickers, rsis, color=rsi_colors)
    axes[0][1].axvline(x=30, color="#2ecc71", linestyle="--", alpha=0.7, label="Oversold")
    axes[0][1].axvline(x=70, color="#e74c3c", linestyle="--", alpha=0.7, label="Overbought")
    axes[0][1].set_xlim(0, 100)
    axes[0][1].set_xlabel("RSI")
    axes[0][1].set_title("RSI by Ticker")
    axes[0][1].legend(fontsize=8)

    # 3: Signal scores
    scores = [s["signal"]["score"] for s in all_signals]
    score_colors = [SIGNAL_COLORS.get(s["signal"]["signal"], "#95a5a6") for s in all_signals]
    axes[1][0].bar(tickers, scores, color=score_colors)
    axes[1][0].axhline(y=0, color="gray", linewidth=0.5)
    axes[1][0].set_ylabel("Signal Score")
    axes[1][0].set_title("Composite Signal Scores")

    # 4: Volatility vs Momentum scatter
    vols = [s["indicators"]["volatility"] * 100 for s in all_signals]
    moms = [s["indicators"]["momentum"] * 100 for s in all_signals]
    scatter_colors = [SIGNAL_COLORS.get(s["signal"]["signal"], "#95a5a6") for s in all_signals]
    axes[1][1].scatter(vols, moms, c=scatter_colors, s=100, edgecolors="black", linewidth=0.5)
    for i, t in enumerate(tickers):
        axes[1][1].annotate(t, (vols[i], moms[i]), fontsize=8, ha="center", va="bottom")
    axes[1][1].axhline(y=0, color="gray", linewidth=0.5)
    axes[1][1].set_xlabel("Volatility (%)")
    axes[1][1].set_ylabel("Momentum (%)")
    axes[1][1].set_title("Volatility vs Momentum")

    plt.tight_layout()
    path = f"logs/{date_str}_dashboard.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    all_signals = []
    for ticker in TICKERS:
        base = random.uniform(10, 5000)
        candles = [generate_ohlcv(ticker, base * (1 + random.gauss(0, 0.02))) for _ in range(20)]
        indicators = compute_indicators(candles)
        signal = generate_signal(indicators)
        all_signals.append({"ticker": ticker, "latest_price": candles[-1]["close"], "indicators": indicators, "signal": signal})
    all_signals.sort(key=lambda x: x["signal"]["score"], reverse=True)

    yesterday = load_yesterday(date_str)
    delta = compute_delta(all_signals, yesterday)

    ms = {"tickers_scanned": len(TICKERS), "buy_signals": sum(1 for s in all_signals if "BUY" in s["signal"]["signal"]),
          "sell_signals": sum(1 for s in all_signals if "SELL" in s["signal"]["signal"]),
          "hold_signals": sum(1 for s in all_signals if s["signal"]["signal"] == "HOLD")}
    report = {"timestamp": now.isoformat(), "run_id": hashlib.sha256(now.isoformat().encode()).hexdigest()[:10],
              "market_summary": ms, "signals": all_signals, "delta": delta}

    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{date_str}.json", "w") as f:
        json.dump(report, f, indent=2)

    chart_path = generate_charts(all_signals, date_str)

    md = [f"# Market Signal Report — {date_str}\n"]
    md.append(f"**Run ID:** `{report['run_id']}` | **Buy:** {ms['buy_signals']} | **Sell:** {ms['sell_signals']} | **Hold:** {ms['hold_signals']}\n")
    md.append(f"![Dashboard]({os.path.basename(chart_path)})\n")
    md.append("## Signal Dashboard\n")
    md.append("| Ticker | Price | Signal | Score | RSI | Momentum | Confidence |")
    md.append("|--------|-------|--------|-------|-----|----------|------------|")
    for s in all_signals:
        md.append(f"| {s['ticker']} | ${s['latest_price']} | **{s['signal']['signal']}** | {s['signal']['score']} | {s['indicators']['rsi']} | {s['indicators']['momentum']} | {s['signal']['confidence']} |")
    if delta.get("status") == "compared":
        md.append("\n## Delta vs Yesterday\n")
        md.append("| Ticker | Today | Yesterday | Price Change | Signal Changed |")
        md.append("|--------|-------|-----------|-------------|----------------|")
        for t, d in delta["deltas"].items():
            arrow = "📈" if d["price_change_pct"] > 0 else "📉"
            changed = "⚠️ YES" if d["signal_changed"] else "—"
            md.append(f"| {t} | {d['today_signal']} | {d['yesterday_signal']} | {arrow} {d['price_change_pct']}% | {changed} |")

    with open(f"logs/{date_str}.md", "w") as f:
        f.write("\n".join(md))
    print("[automated-bots] v2.0 report + charts generated")

if __name__ == "__main__":
    main()
