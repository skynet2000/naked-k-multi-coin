import urllib.request, json, datetime, csv, time

# 动态计算：当前时间往前推30天
now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
start_ts = now_ms - 30 * 24 * 3600 * 1000

all_candles = []
after = now_ms  # 从当前时间往前翻

while True:
    url = f"https://www.okx.com/api/v5/market/history-candles?instId=TRX-USDT-SWAP&bar=1H&limit=100&after={after}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        if data.get("code") != "0" or not data.get("data"):
            print(f"API error: {data}")
            break
        batch = data["data"]
        print(f"Batch: {len(batch)} candles, last ts={batch[-1][0]}")
        all_candles.extend(batch)
        last_ts = int(batch[-1][0])
        after = last_ts  # 继续往前翻
        time.sleep(0.2)  # 避免限速
        if last_ts <= start_ts or len(batch) < 100:
            break
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"\nTotal candles fetched: {len(all_candles)}")
if all_candles:
    all_candles.sort(key=lambda x: int(x[0]))
    ts_first = int(all_candles[0][0])
    ts_last = int(all_candles[-1][0])
    print(f"Range: {datetime.datetime.fromtimestamp(ts_first/1000)} -> {datetime.datetime.fromtimestamp(ts_last/1000)}")
    with open("C:/Users/MECHREVO/.qclaw/workspace-agent-ca7a859e/trx_1h.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close", "vol", "quote_vol", "confirm"])
        for c in all_candles:
            w.writerow(c)
    print("Saved to trx_1h.csv")
