# Naked-K-Multi-Coin · 裸K突破策略

> 多币种裸K突破策略 · 激进版（v1.2.0） · GitHub: [skynet2000/naked-k-multi-coin](https://github.com/skynet2000/naked-k-multi-coin)

---

## 策略简介

每15分钟自动扫描 **10个精选主流币**，基于300根K线识别结构、构建箱体、评估质量，执行激进突破回踩交易，支持动态仓位和全持仓管理。

**⚠️ 免责声明**：本策略为第三方社区作品，**不代表 OKX 官方立场**，仅通过 OKX 公共 API 获取市场数据。通知渠道 Webhook 地址须由用户自行在运行时配置，策略本身不内置任何地址。

---

## 目录结构

```
naked-k-multi-coin/
├── SKILL.md                              策略完整文档（含信号逻辑、参数配置、交易规则）
├── README.md                             本文件
├── scripts/
│   ├── backtest_naked_k.py               回测引擎（Python，详见下方）
│   ├── fetch_trx.py                      OKX K线数据拉取脚本
│   └── signal_engine.py                  信号评分引擎（从 SKILL.md 提取）
└── reports/
    └── naked-k-multi-coin/
        └── backtest_report.md            TRX-USDT-SWAP 回测报告（2026-03-11 ~ 2026-04-13）
```

---

## 脚本说明

| 脚本 | 用途 | 依赖 |
|------|------|------|
| `scripts/fetch_trx.py` | 从 OKX 公共 API 拉取历史K线数据（无需 API Key） | Python 标准库 |
| `scripts/backtest_naked_k.py` | 基于裸K形态（Pin Bar / 吞没）执行完整回测，输出交易明细和绩效指标 | Python 标准库 |
| `scripts/signal_engine.py` | 信号评分引擎（RSI + EMA 双信号），含ATR动态止损/止盈/移动止盈工具函数 | Python 标准库 |

---

## 快速开始

```bash
# 1. 拉取数据（无需 API Key，直接调用 OKX 公共接口）
python scripts/fetch_trx.py

# 2. 运行回测（输出绩效报告）
python scripts/backtest_naked_k.py
```

> **注意**：回测结果仅为历史数据回顾，不构成任何投资建议。加密货币合约交易存在极高风险，可能导致全部本金损失。

---

## 支持交易对

BTC-USDT-SWAP · ETH-USDT-SWAP · SOL-USDT-SWAP · BNB-USDT-SWAP  
XRP-USDT-SWAP · ADA-USDT-SWAP · DOGE-USDT-SWAP · AVAX-USDT-SWAP  
TRX-USDT-SWAP · HYPE-USDT-SWAP

---

## 核心参数（可调）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 杠杆 | 3× | 建议 2× 降低回撤 |
| 单笔风险比例 | 2% | 每笔交易占账户比例 |
| ATR止损倍数 | 0.8 | 建议 1.2 减少噪音触发 |
| 止盈风险比 | 1:2 | R/R = 1:2 |
| 最小ATR过滤 | 无 | 建议 ≥$0.0005 |
| 最大同时持仓 | 5 | 全币种并行 |

---

## 安全说明

- ✅ 本仓库**不包含**任何 API Key、Secret 或 Webhook 地址
- ✅ 所有脚本使用 OKX **公共市场 API**，无需认证
- ✅ 通知功能（如需飞书/钉钉推送）须用户自行在 `SKILL.md` 中配置个人 Webhook
