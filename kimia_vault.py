import json
import hashlib
import datetime

class LocalVault:
    def __init__(self, db_file):
        self.db_file = db_file

    def _generate_hash(self, data):
        return hashlib.sha256(data.encode()).hexdigest()

    # --- این قسمتی است که شما باید اضافه کنید ---
    def issue_shares(self, asset_hash, shareholder_id, percentage):
        """ثبت سهامداری برای یک دارایی خاص با شفافیت کامل"""
        share_data = f"ASSET:{asset_hash}|HOLDER:{shareholder_id}|SHARE:{percentage}%"
        share_hash = self._generate_hash(share_data)

        share_record = {
            "timestamp": str(datetime.datetime.now()),
            "type": "EQUITY_ISSUE",
            "asset_hash": asset_hash,
            "shareholder": shareholder_id,
            "percentage": percentage,
            "proof": share_hash
        }

        with open("equity_ledger.jsonl", "a") as f:
            f.write(json.dumps(share_record) + "\n")
        
        return share_record
    # ------------------------------------------

    # سایر متدها مثل add_asset و غیره...

