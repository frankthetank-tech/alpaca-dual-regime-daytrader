# Strategy #3: Dual-Regime Long/Short Day Trading Bot (ORB-15 Cond 4 V2)

Autonomous institutional day trading system implementing **Opening Range Breakout (ORB-15 Cond 4 V2)** on **Alpaca Markets**.

---

## 1. Strategy Architecture & Core Principles

- **Zero Overnight Risk:** 100% Cash at market close every single day. Zero overnight margin interest ($0.00).
- **Dynamic Intraday Leverage:** 100% Margin (2.0x Buying Power default), strictly whole shares.
- **09:45 AM Macro Regime Shield (Cond 4 V2):**
  - Evaluated point-in-time at 09:45:04 AM using SPY's price relative to its 50-day SMA, 200-day SMA, and Today's Open.
  - **Bullish Regime:** SPY[09:45] > SMA200 AND SPY[09:45] > SMA50 $\rightarrow$ **Long Engine Only**.
  - **Bearish Red Regime:** (SPY[09:45] < SMA200 OR SPY[09:45] < SMA50) AND (SPY[09:45] < SPY[Open]) $\rightarrow$ **Short Engine Only**.
  - **Neutral / Defensive Cash:** SPY below SMAs but green intraday (bear rally) $\rightarrow$ **100% Cash (Stand Down)**.
- **Microstructure Setup Filters:**
  - Volatility Expansion: 20-day $\text{ATR}\% \ge 1.5\%$.
  - Catalyst Volume: Opening 15-minute $\text{RVOL} \ge 1.25\times$.
  - Longs: Day Open > SMA50, Gap $\ge +0.3\%$, **Gap $\le +4.5\%$ (Extreme Gap-and-Trap Circuit Breaker)**.
  - Shorts: Day Open < SMA50, Gap $\le -0.3\%$.
- **Dynamic ATR-Scaled Profit Target:**
  $$\text{Target \%} = \max(2.0\%, \min(4.5\%, 1.5 \times \text{ATR}\%_{20}))$$
- **Dynamic Account-Tier Sizing (Whole Shares Only):**
  - Account < $15k USD: Max 2 positions (50% BP each).
  - Account $15k – $50k USD: Max 3 positions (33.3% BP each).
  - Account $50k – $150k USD: Max 4 positions (25% BP each).
  - Account $150k – $500k USD: Max 5 positions (20% BP each).
  - Account > $500k USD: Max 8 positions (12.5% BP each).
  - Strictly integer floor whole shares ($\lfloor \text{Alloc} / \text{Price} \rfloor$).
- **Permanent Structural Blacklist:**
  - 228 confirmed toxic drag assets (Commercial banks, regulated utilities, low-beta staples, commodity/bond ETFs) are permanently ignored.
- **Execution via Native Alpaca Matching Engine:**
  - Submits native bracket stop orders directly to Alpaca matching engine:
    - **Long:** Buy-Stop at OR15 High, Stop Loss at $-1.2\%$, Dynamic Profit Target at $+2.0\%$ to $+4.5\%$.
    - **Short:** Sell-Stop at OR15 Low, Stop Loss at $+1.2\%$, Dynamic Profit Target at $-2.0\%$ to $-4.5\%$.
- **11:30 AM Entry Cutoff:** Cancels unfilled resting entry orders so capital remains 100% cash if no breakout occurs.
- **15:45 PM MOC Liquidation:** Closes all open positions and resting orders to guarantee 100% cash before 16:00 close.

---

## 2. GitHub Actions Automated Cloud Schedule (Mon-Fri)

1. **09:25 AM EDT (13:25 UTC):** 20-Minute Early Warmup, Pre-fetch Daily Metrics & 09:45:04 AM Precision Execution (`python main.py --warmup`)
2. **11:30 AM EDT (15:30 UTC):** Cancel Unfilled Resting Entry Orders (`python main.py --cutoff`)
3. **03:30 PM EDT (19:30 UTC):** Early MOC Liquidation to ensure 100% Cash before 4:00 PM close (`python main.py --moc`)

---

## 3. Required GitHub Repository Secrets

Configure the following secrets in **Settings > Secrets and variables > Actions**:
- `ALPACA_API_KEY`: Your Alpaca API Key ID (Paper or Live)
- `ALPACA_SECRET_KEY`: Your Alpaca Secret Key (Paper or Live)
