#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RECONNECT — همه شاخه‌ها، یکجا، وصل"""

import asyncio, json, os, time, hashlib, urllib.request
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
ADDR = open(os.path.join(HOME, "wallet_address.txt")).read().strip()
OUT  = os.path.join(HOME, "KIMIA_GLOBAL", "record", "reconnect.jsonl")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def get(u, t=15):
    try:
        with urllib.request.urlopen(u, timeout=t) as r:
            return r.read()[:2000]
    except Exception as e:
        return f"ERR:{e}".encode()

SOURCES = {
    # کیف پول
    "wallet_main":   f"https://api.trongrid.io/v1/accounts/{ADDR}",
    "wallet_scan":   f"https://apilist.tronscanapi.com/api/accountv2?address={ADDR}",
    "tx_trx":        f"https://api.trongrid.io/v1/accounts/{ADDR}/transactions?limit=50",
    "tx_trc20":      f"https://api.trongrid.io/v1/accounts/{ADDR}/transactions/trc20?limit=50",
    # بازار جهانی
    "price_cg":      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tron,tether&vs_currencies=usd",
    "price_binance": "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
    "price_coinbase":"https://api.coinbase.com/v2/prices/BTC-USD/spot",
    "price_kraken":  "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
    # ارز فیات
    "fiat_frank":    "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,IRR",
    "fiat_host":     "https://api.exchangerate.host/latest?base=USD",
    # خبر جهانی
    "news_ct":       "https://cointelegraph.com/rss",
    "news_cd":       "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "news_bbc":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    "news_reuters":  "https://feeds.reuters.com/reuters/businessNews",
    "news_hn":       "https://hacker-news.firebaseio.com/v0/topstories.json",
    # زمان جهانی
    "time_utc":      "https://worldtimeapi.org/api/timezone/Etc/UTC",
    "time_tehran":   "https://worldtimeapi.org/api/timezone/Asia/Tehran",
    # داده‌های جهانی
    "github":        "https://api.github.com/zen",
    "space_iss":     "http://api.open-notify.org/iss-now.json",
    "weather":       "https://wttr.in/?format=j1",
}

async def fetch_all():
    loop = asyncio.get_event_loop()
    async def one(name, url):
        return name, await loop.run_in_executor(None, get, url)
    tasks = [one(n, u) for n, u in SOURCES.items()]
    return dict(await asyncio.gather(*tasks))

async def main():
    print("═" * 60)
    print("RECONNECT — همه شاخه‌ها، وصل")
    print("═" * 60)
    print("آدرس:", ADDR)
    print()

    t0 = time.perf_counter()
    results = await fetch_all()
    t1 = time.perf_counter()

    ok, err = 0, 0
    for name, raw in results.items():
        s = raw.decode(errors="ignore") if isinstance(raw, bytes) else str(raw)
        if s.startswith("ERR"):
            print(f"  ❌ {name:15s} {s[:50]}")
            err += 1
        else:
            print(f"  ✅ {name:15s} {len(s)} bytes")
            ok += 1

    print(f"\n✅ {ok}  ❌ {err}  ⏱️ {t1-t0:.3f}s")

    # ثبت
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ns": time.time_ns(),
        "addr": ADDR,
        "ok": ok, "err": err,
        "results": {k: (v.decode(errors="ignore")[:200] if isinstance(v, bytes) else str(v)[:200]) for k, v in results.items()},
    }
    rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nهش : {rec['hash'][:32]}")
    print(f"فایل: {OUT}")

asyncio.run(main())
