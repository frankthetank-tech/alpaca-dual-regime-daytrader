# Strategy #3: Dual-Regime Long/Short Day Trading Bot (Alpaca Cloud)

Autonomous institutional day trading system implementing **Strategy #3: Dual-Regime Intraday Long/Short Day Trading Strategy** on **Alpaca Markets**.

---

## 1. Strategy Architecture & Core Principles

- **Zero Overnight Risk:** 100% Cash at market close every single day.
- **Zero Leverage:** Trades at 1.0x cash allocation without borrowed money or toxic leveraged ETFs.
- **09:45 AM Macro Regime Shield:**
  - Evaluated point-in-time at 09:45 AM using SPY's price relative to its 50-day and 200-day SMAs.
  - **Bullish Regime:** SPY[09:45] > SMA200 AND SPY[09:45] > SMA50 $\rightarrow$ **Long Engine Only**.
  - **Bearish Regime:** SPY[09:45] < SMA200 OR SPY[09:45] < SMA50 $\rightarrow$ **Short Engine Only**.
- **Catalyst Screening:**
  - Ranks overnight gap catalysts with heavy morning volume ($\text{RVOL}_{15} \ge 1.25\times$).
  - Selects the **#1 Rank Leader** exclusively.
- **Execution via Native Matching Engine:**
  - Submits native bracket stop orders directly to Alpaca matching engine:
    - **Long:** Buy-Stop at OR15 High, Stop Loss at $-1.2\%$, Profit Target at $+3.5\%$.
    - **Short:** Sell-Stop at OR15 Low, Stop Loss at $+1.2\%$, Profit Target at $-3.5\%$.
- **11:30 AM Entry Cutoff:** Cancels unfilled entry orders so capital remains 100% cash if no breakout occurs.
- **15:55 PM MOC Liquidation:** Liquidates any remaining open position into the close.

---

## 2. GitHub Actions Automated Cloud Schedule (Mon-Fri)

1. **09:45 AM EDT (13:45 UTC):** Run Macro Shield & Order Placement (`python main.py --scan`)
2. **11:30 AM EDT (15:30 UTC):** Cancel Unfilled Entry Orders (`python main.py --cutoff`)
3. **03:55 PM EDT (19:55 UTC):** Market-on-Close Exit (`python main.py --moc`)

---

## 3. Required GitHub Repository Secrets

- `ALPACA_API_KEY`: Alpaca Paper API Key (`PKPNBG2JCQHNYC436SIQAGF5WC`)
- `ALPACA_SECRET_KEY`: Alpaca Paper API Secret (`5L1NMQPYK9mQSojm91geZHytfsdbrMaSCp5r56AyKgWE`)
