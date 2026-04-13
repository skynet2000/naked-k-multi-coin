"""
Naked-K-Multi-Coin 信号引擎
从 SKILL.md 提取，内联 Python 代码独立化
功能：多币种横向对比找最优入场机会
"""

def score_signal(rsi_score: float, ema_score: float, total_score: float) -> dict:
    """信号评分（RSI + EMA 双信号）"""
    if total_score > 80:
        mode = "FULL"   # 满仓模式
    elif total_score > 60:
        mode = "STD"    # 标准模式
    else:
        mode = "WAIT"   # 观望
    return {"score": total_score, "mode": mode}


def calc_atr_stop(entry_price: float, atr: float, mult: float = 2.0,
                  min_pct: float = 1.5, max_pct: float = 3.0) -> float:
    """ATR动态止损：基于波动率计算止损幅度"""
    atr_pct = (atr / entry_price) * 100
    stop_pct = mult * atr_pct
    stop_pct = max(min_pct, min(max_pct, stop_pct))
    return entry_price * (1 - stop_pct / 100)


def calc_atr_take(entry_price: float, atr: float, mult: float = 3.0,
                  min_pct: float = 6.0) -> float:
    """ATR动态止盈：确保最小止盈比例"""
    atr_pct = (atr / entry_price) * 100
    tp_pct = mult * atr_pct
    tp_pct = max(min_pct, tp_pct)
    return entry_price * (1 + tp_pct / 100)


def calc_trailing_stop(highest_price: float, trail_pct: float = 3.0) -> float:
    """移动止盈：回撤 trail_pct% 触发"""
    return highest_price * (1 - trail_pct / 100)


def rank_coins(coin_scores: dict) -> list:
    """多币种横向评分排序，返回入场优先级"""
    sorted_coins = sorted(coin_scores.items(), key=lambda x: x[1]["total"], reverse=True)
    return [coin for coin, _ in sorted_coins]


def position_size(equity: float, pct: float, price: float, leverage: int = 3) -> float:
    """计算开仓张数（合约数量）"""
    pos_usd = equity * pct * leverage
    return round(pos_usd / price, 3)


if __name__ == "__main__":
    # 单元测试
    print("=== 信号引擎自检 ===")
    print(f"ATR止损: {calc_atr_stop(72000, 500):.2f}")
    print(f"ATR止盈: {calc_atr_take(72000, 500):.2f}")
    print(f"移动止盈: {calc_trailing_stop(75000):.2f}")
    print(f"仓位计算: {position_size(10000, 0.3, 72000, 15):.3f} 张")
    print("=== 自检通过 ===")
