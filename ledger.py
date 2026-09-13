import hashlib, json, os
from datetime import datetime

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "equity_ledger.jsonl")

def make_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def last_line(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    return lines[-1] if lines else None

def append_event(event: dict) -> dict:
    prev_raw = last_line(LEDGER)
    prev = "GENESIS" if prev_raw is None else make_hash(prev_raw)
    event["prev_hash"] = prev
    event["timestamp"] = datetime.now().isoformat()
    proof = make_hash(json.dumps(event, sort_keys=True, ensure_ascii=False))
    record = {**event, "proof": proof}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("EVENT SECURED:", record["type"], "→", proof[:16], "…")
    return record

if __name__ == "__main__":
    import sys
    event = {"type": sys.argv[1] if len(sys.argv) > 1 else "GENESIS_MIGRATION",
             "note": "chain-linked ledger starts here",
             "migrated_last": make_hash(last_line(LEDGER)) if last_line(LEDGER) else None}
    append_event(event)

