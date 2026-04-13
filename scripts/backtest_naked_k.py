"""
Naked-K-Multi-Coin 回测引擎
标的: TRX-USDT-SWAP (OKX永续)
时间框架: 1H
回测周期: ~30天
"""

import csv, math, datetime

# ─── 参数配置 ───────────────────────────────────────────
INIT_CAPITAL   = 1000.0       # 初始资金 USDT
LEVERAGE       = 3            # 固定杠杆
RISK_PCT       = 0.02         # 每笔风险敞口比例
RR_RATIO       = 2.0          # 止盈风险收益比
ATR_PERIOD     = 14           # ATR周期
ATR_MULTI_SL    = 0.8          # ATR倍数 -> 止损
CONFIRM_BARS    = 1            # 信号确认所需K线数
FEE_TAKER      = 0.0005       # 吃单手续费 (0.05%)
FEE_MAKER      = 0.0002       # 挂单手续费 (0.02%)
                                       # (保守取 0.01%/天)
MAX_POSITIONS   = 1           # 最大同时持仓数
# ──────────────────────────────────────────────────────────

def load_csv(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["ts"]        = int(row["ts"])
            row["open"]      = float(row["open"])
            row["high"]      = float(row["high"])
            row["low"]       = float(row["low"])
            row["close"]     = float(row["close"])
            row["vol"]       = float(row["vol"])
            row["quote_vol"] = float(row["quote_vol"])
            rows.append(row)
    return rows

def calc_atr(rows, period=14):
    trs = []
    for i, r in enumerate(rows):
        if i == 0:
            tr = r["high"] - r["low"]
        else:
            hl  = r["high"]  - r["low"]
            hc  = abs(r["high"]  - rows[i-1]["close"])
            cl  = abs(r["low"]   - rows[i-1]["close"])
            tr  = max(hl, hc, cl)
        trs.append(tr)
    if len(trs) < period:
        return [trs[i] if i < len(trs) else 0 for i in range(len(trs))]
    atr = sum(trs[:period]) / period
    atrs = [atr]
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
        atrs.append(atr)
    atrs = [0.0] * (period - 1) + atrs
    return atrs

def is_bullish_engulfing(b1, b2):
    c1, o1 = b1["close"], b1["open"]
    c2, o2 = b2["close"], b2["open"]
    prevBear = c1 < o1
    currBull = c2 > o2
    body1 = abs(c1 - o1)
    body2 = c2 - o2
    fullEngulf = (o2 <= c1 and c2 >= o1)
    return prevBear and currBull and body2 > body1 * 0.8 and fullEngulf

def is_bearish_engulfing(b1, b2):
    c1, o1 = b1["close"], b1["open"]
    c2, o2 = b2["close"], b2["open"]
    prevBull = c1 > o1
    currBear = c2 < o2
    body1 = abs(c1 - o1)
    body2 = abs(c2 - o2)
    fullEngulf = (c2 <= o1 and o2 >= c1)
    return prevBull and currBear and body2 > body1 * 0.8 and fullEngulf

def is_pinbar_bull(bars, i, atr):
    b = bars[i]
    o, c, h, l = b["open"], b["close"], b["high"], b["low"]
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    avg_body = body if body > 1e-8 else (atr[i] * 0.01)
    return (lower >= avg_body * 2.5 and upper <= avg_body * 0.4 and lower > atr[i] * 0.5)

def is_pinbar_bear(bars, i, atr):
    b = bars[i]
    o, c, h, l = b["open"], b["close"], b["high"], b["low"]
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    avg_body = body if body > 1e-8 else (atr[i] * 0.01)
    return (upper >= avg_body * 2.5 and lower <= avg_body * 0.4 and upper > atr[i] * 0.5)

def detect_support_resistance(bars, lookback=20):
    if len(bars) < lookback:
        return None, None
    recent = bars[-lookback:]
    lows  = [b["low"]  for b in recent]
    highs = [b["high"] for b in recent]
    sorted_lows  = sorted(lows)
    sorted_highs = sorted(highs)
    n = max(1, len(lows) // 3)
    support = sum(sorted_lows[:n])  / n
    resist  = sum(sorted_highs[-n:]) / n
    return support, resist

def run_backtest(bars, initial_capital=1000, leverage=3, risk_pct=0.02):
    capital       = initial_capital
    capital_curve = [initial_capital]
    atrs          = calc_atr(bars, ATR_PERIOD)
    trades        = []
    pos           = None

    for i in range(2, len(bars)):
        b0 = bars[i - 2]
        b1 = bars[i - 1]
        b2 = bars[i]

        support, resist = detect_support_resistance(bars[:i+1], lookback=20)
        atr  = atrs[i] if i < len(atrs) else atrs[-1]
        price = b1["close"]

        # ── 持仓管理 ──────────────────────────────────────
        if pos:
            direction   = pos["direction"]
            entry_price = pos["entry_price"]
            stop_loss   = pos["stop_loss"]
            take_profit = pos["take_profit"]
            pos_size    = pos["size"]
            trail_active = pos.get("trail_active", False)
            trail_price  = pos.get("trail_price", 0)
            bar_high = b1["high"]
            bar_low  = b1["low"]

            # 止损
            if direction == 1 and bar_low  <= stop_loss:
                pnl = (stop_loss - entry_price) * pos_size * leverage - pos["fee"]
                capital += pnl
                trades.append({**pos, "exit_price": stop_loss, "exit_reason": "SL", "pnl_usdt": pnl, "idx": i})
                pos = None
            elif direction == -1 and bar_high >= stop_loss:
                pnl = (entry_price - stop_loss) * pos_size * leverage - pos["fee"]
                capital += pnl
                trades.append({**pos, "exit_price": stop_loss, "exit_reason": "SL", "pnl_usdt": pnl, "idx": i})
                pos = None
            # 移动止损触发
            elif direction == 1 and trail_active and bar_low  <= trail_price:
                pnl = (trail_price - entry_price) * pos_size * leverage - pos["fee"]
                capital += pnl
                trades.append({**pos, "exit_price": trail_price, "exit_reason": "TS", "pnl_usdt": pnl, "idx": i})
                pos = None
            elif direction == -1 and trail_active and bar_high >= trail_price:
                pnl = (entry_price - trail_price) * pos_size * leverage - pos["fee"]
                capital += pnl
                trades.append({**pos, "exit_price": trail_price, "exit_reason": "TS", "pnl_usdt": pnl, "idx": i})
                pos = None
            # 固定止盈
            elif direction == 1 and bar_high >= take_profit:
                pnl = (take_profit - entry_price) * pos_size * leverage - pos["fee"]
                capital += pnl
                trades.append({**pos, "exit_price": take_profit, "exit_reason": "TP", "pnl_usdt": pnl, "idx": i})
                pos = None
            elif direction == -1 and bar_low  <= take_profit:
                pnl = (entry_price - take_profit) * pos_size * leverage - pos["fee"]
                capital += pnl
                trades.append({**pos, "exit_price": take_profit, "exit_reason": "TP", "pnl_usdt": pnl, "idx": i})
                pos = None
            # 激活移动止损
            elif not trail_active:
                profit_pct = (price - entry_price) / entry_price * leverage if direction == 1 else (entry_price - price) / entry_price * leverage
                if profit_pct >= 0.02:
                    pos["trail_active"] = True
                    pos["trail_price"] = entry_price + (atr * 0.5 if direction == 1 else -atr * 0.5)
            # 实时更新移动止损线
            if pos and pos.get("trail_active"):
                if direction == 1:
                    new_trail = bar_low - atr * 0.3
                    if new_trail > pos["trail_price"]:
                        pos["trail_price"] = new_trail
                else:
                    new_trail = bar_high + atr * 0.3
                    if new_trail < pos["trail_price"]:
                        pos["trail_price"] = new_trail

        # ── 开仓信号 ──────────────────────────────────────
        if not pos:
            signal    = None
            conf_bars = 0
            for offset in range(CONFIRM_BARS):
                ci = i - offset
                if ci < 2:
                    break
                bb = bars[ci - 1]
                bc = bars[ci]
                close_near_support = support and bc["close"] < support * 1.02 and bc["close"] > support * 0.98
                close_near_resist  = resist  and bc["close"] > resist  * 0.98 and bc["close"] < resist  * 1.02

                if (is_pinbar_bull(bars, ci, atrs) or
                    (is_bullish_engulfing(bb, bc) and close_near_support)):
                    signal    = 1
                    conf_bars += 1
                elif (is_pinbar_bear(bars, ci, atrs) or
                      (is_bearish_engulfing(bb, bc) and close_near_resist)):
                    signal    = -1
                    conf_bars += 1

            if conf_bars >= CONFIRM_BARS:
                direction  = signal
                sl_price   = (bars[i]["low"]  - atr * ATR_MULTI_SL * 0.5) if direction == 1 else (bars[i]["high"] + atr * ATR_MULTI_SL * 0.5)
                risk_dist  = abs(bars[i]["close"] - sl_price)
                tp_price   = bars[i]["close"] + risk_dist * RR_RATIO * direction
                risk       = risk_dist * leverage
                risk_usdt  = capital * RISK_PCT
                size       = risk_usdt / risk if risk > 0 else 0
                fee        = bars[i]["close"] * size * FEE_TAKER

                if size >= 1:
                    pos = {
                        "direction":   direction,
                        "entry_price":  bars[i]["close"],
                        "stop_loss":    sl_price,
                        "take_profit":  tp_price,
                        "size":         size,
                        "fee":          fee,
                        "idx_entry":    i,
                        "entry_time":   datetime.datetime.fromtimestamp(bars[i]["ts"]/1000).strftime("%Y-%m-%d %H:%M"),
                        "trail_active": False,
                        "trail_price":  0,
                    }

        capital_curve.append(capital)

    # 期末平仓
    if pos:
        exit_p = bars[-1]["close"]
        if pos["direction"] == 1:
            pnl = (exit_p - pos["entry_price"]) * pos["size"] * leverage - pos["fee"]
        else:
            pnl = (pos["entry_price"] - exit_p) * pos["size"] * leverage - pos["fee"]
        capital += pnl
        trades.append({**pos, "exit_price": exit_p, "exit_reason": "END", "pnl_usdt": pnl, "idx": len(bars)-1})
        capital_curve.append(capital)

    return capital, capital_curve, trades

# ─── 主程序 ──────────────────────────────────────────────
bars = load_csv("C:/Users/MECHREVO/.qclaw/workspace-agent-ca7a859e/trx_1h.csv")
print(f"Klines: {len(bars)}")
print(f"Period: {datetime.datetime.fromtimestamp(bars[0]['ts']/1000)} -> {datetime.datetime.fromtimestamp(bars[-1]['ts']/1000)}")

final_cap, curve, trades = run_backtest(bars)

pnls     = [t["pnl_usdt"] for t in trades]
n_total  = len(trades)
n_win    = sum(1 for p in pnls if p > 0)
n_loss   = n_total - n_win
win_rate = n_win / n_total * 100 if n_total else 0
avg_win  = sum(p for p in pnls if p > 0) / n_win if n_win else 0
avg_loss = sum(p for p in pnls if p < 0) / n_loss if n_loss else 0
total_pnl = sum(pnls)
max_dd   = 0
peak     = INIT_CAPITAL
for v in curve:
    if v > peak: peak = v
    dd = (peak - v) / peak * 100
    if dd > max_dd: max_dd = dd
sharpe  = 0
if len(pnls) > 1:
    mean_r = sum(pnls) / len(pnls)
    std_r  = math.sqrt(sum((x - mean_r)**2 for x in pnls) / len(pnls))
    sharpe = mean_r / std_r * math.sqrt(252) if std_r > 0 else 0

roi = (final_cap - INIT_CAPITAL) / INIT_CAPITAL * 100

# 输出报告
report = []
report.append("=" * 60)
report.append("  Naked-K-Multi-Coin Backtest Report")
report.append("  TRX-USDT-SWAP | 1H | {} days".format(len(bars)//24))
report.append("=" * 60)
report.append(f"  Initial Capital     : ${INIT_CAPITAL:.2f}")
report.append(f"  Final Capital      : ${final_cap:.2f}")
report.append(f"  Total PnL          : ${total_pnl:.2f}  (ROI: {roi:.2f}%)")
report.append(f"  Annualized (est.)   : {roi/33*365:.1f}%")
report.append(f"  Leverage            : {LEVERAGE}x")
report.append(f"  Risk per Trade     : {RISK_PCT*100:.0f}% of capital")
report.append("")
report.append(f"  Total Trades       : {n_total}")
report.append(f"  Win                : {n_win} ({win_rate:.1f}%)")
report.append(f"  Loss               : {n_loss}")
report.append(f"  Avg Win            : +${avg_win:.2f}")
report.append(f"  Avg Loss           : -${abs(avg_loss):.2f}")
report.append(f"  Profit Factor      : {abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "  Profit Factor      : N/A")
report.append("")
report.append(f"  Max Drawdown       : {max_dd:.2f}%")
report.append(f"  Sharpe Ratio(ann.) : {sharpe:.2f}")
report.append("")
report.append("  Exit Reasons:")
reasons = {}
for t in trades:
    r = t["exit_reason"]
    reasons[r] = reasons.get(r, 0) + 1
labels = {"SL": "StopLoss", "TP": "TakeProfit", "TS": "TrailStop", "END": "EndClose"}
for k, v in sorted(reasons.items()):
    report.append(f"    {labels.get(k,k)}: {v} trades")
report.append("")
report.append("  Last 15 Trades:")
report.append(f"  {'#':>3}  {'Time':<16}  {'Dir':>3}  {'Entry':>8}  {'Exit':>8}  {'PnL($)':>8}  {'Reason'}")
for idx, t in enumerate(trades[-15:], len(trades)-14):
    dir_s = "LONG" if t["direction"] == 1 else "SHORT"
    report.append(f"  {idx:>3}  {t['entry_time']:<16}  {dir_s:>3}  {t['entry_price']:>8.4f}  {t['exit_price']:>8.4f}  {t['pnl_usdt']:>+8.2f}  {t['exit_reason']}")

report.append("")
report.append("=" * 60)

output = "\n".join(report)
print(output)

with open("C:/Users/MECHREVO/.qclaw/workspace-agent-ca7a859e/backtest_report.txt", "w", encoding="utf-8") as f:
    f.write(output)
print("\nReport saved to backtest_report.txt")
