# Naked-K-Multi-Coin · 裸K突破策略

> 多币种裸K突破策略 · 激进版（v1.2.0）

## 策略简介

每15分钟扫描10个精选主流币，基于300根K线识别结构、构建箱体、评估质量，执行激进突破回踩交易，支持动态仓位和全持仓管理。

## 目录结构

```
SKILL.md                          策略文档
scripts/
  backtest_naked_k.py             回测引擎
  signal_engine.py                信号评分引擎（SKILL.md提取）
  fetch_trx.py                    OKX K线数据拉取
reports/
  naked-k-multi-coin/
    backtest_report.md            TRX-USDT-SWAP 回测报告
data/                             市场数据（不提交）
```

## 快速开始

```bash
# 拉取数据并回测
python scripts/fetch_trx.py
python scripts/backtest_naked_k.py
```

## 免责声明

本策略为第三方社区作品，与 OKX 官方无关。
