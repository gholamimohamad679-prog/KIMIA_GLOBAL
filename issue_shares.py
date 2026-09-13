import json
import hashlib
import datetime


def make_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def issue_shares(asset_hash, shareholder_id, percentage):
    share_data = f"ASSET:{asset_hash}|HOLDER:{shareholder_id}|SHARE:{percentage}%"
    share_hash = make_hash(share_data)
    share_record = {
        "type": "EQUITY_ISSUE",
        "asset_hash": asset_hash,
        "shareholder": shareholder_id,
        "percentage": percentage,
        "timestamp": datetime.datetime.now().isoformat(),
        "proof": share_hash,
    }
    with open("equity_ledger.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(share_record, ensure_ascii=False) + "\n")
    print("RECORD SECURED")
    return share_record


if __name__ == "__main__":
    issue_shares(
        asset_hash=make_hash("KIMIA_VALUE_UNIT_001"),
        shareholder_id="YOVARNOVA_ADMIN",
        percentage=100,
    )
