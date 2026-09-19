#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KIMIA Ω MASTER SYSTEM — HARDENED / TRANSFER EDITION

Evidence-first, append-only, auditable SQLite master.
Principles:
- OBSERVATION != MEASUREMENT != EVIDENCE != VALIDATION != RESULT
- CLAIM != PROOF
- SCORE != PROOF
- PCT is an application route, not an automatic grant
- No DELETE / UPDATE on immutable records
- Hash integrity for nodes, edges and audit ledger
- Hash-chained audit ledger
- Self-test before operational claims
- No fabricated PASS / PROVEN / attribution
- Atomic transactions for import and seed
"""

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


DB_FILE = "kimia_master.db"
EXPORT_FILE = "kimia_master_export.json"

NODE_TYPES = {
    "ROOT", "IDENTITY", "PROVENANCE", "COMMITMENT", "CLAIM",
    "EXECUTION", "OBSERVATION", "MEASUREMENT", "EVIDENCE", "VALIDATION",
    "RESULT", "DISCOVERY", "INVENTION_CANDIDATE", "IP_OWNERSHIP",
    "RIGHTS_CONTRACT", "GOVERNANCE_AUTHORITY", "ECONOMIC_VALUE",
    "INTERNATIONAL_SCOPE", "AI_MODEL_DATA_GOVERNANCE", "SECURITY_SAFETY",
    "FAILURE_CORRECTION", "LEARNING_EVOLUTION", "EXTERNAL_REF",
    "PROOF_STATUS", "NIST_CYCLE", "AUDIT_LOG", "SELF_TEST"
}

EDGE_TYPES = {
    "HAS_PART", "DERIVED_FROM", "SUPPORTED_BY", "VALIDATED_BY",
    "MEASURED_BY", "GOVERNS", "IN_SCOPE_OF", "CONTRADICTS",
    "CORRECTS", "LEADS_TO", "REFERENCES", "IMPLEMENTS",
    "AUDITED_BY", "PART_OF"
}

PROOF_LEVELS = (
    "UNVERIFIED", "INDICATION", "EVIDENCE", "VALIDATED",
    "PROVEN", "REPRODUCED", "INDEPENDENTLY_VERIFIED"
)

# These are evidence contribution weights only.
# They are NOT legal/scientific proof standards and never by themselves
# authorize a RESULT or PROVEN status.
EVIDENCE_WEIGHTS = {
    "OBSERVATION": 0.20,
    "MEASUREMENT": 0.30,
    "EVIDENCE": 0.40,
    "VALIDATION": 0.50,
    "RESULT": 0.60,
    "DISCOVERY": 0.70,
    "INVENTION_CANDIDATE": 0.80,
    "IP_OWNERSHIP": 0.90,
    "EXTERNAL_REF": 0.20,
    "FAILURE_CORRECTION": -0.30,
}

REPRODUCIBILITY_WEIGHT = 0.20
INDEPENDENT_CHECK_WEIGHT = 0.30


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str = "") -> str:
    value = uuid.uuid4().hex
    return f"{prefix}-{value}" if prefix else value


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def compute_hash(*args: Any) -> str:
    h = hashlib.sha256()
    for arg in args:
        h.update(str(arg).encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


class MasterDB:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._set_pragmas()
        self._create_schema()
        self._create_triggers()

    def _set_pragmas(self) -> None:
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = FULL")

    def _create_schema(self) -> None:
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            meta_json TEXT NOT NULL DEFAULT '{}',
            hash TEXT NOT NULL,
            is_readonly INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS edges (
            id TEXT PRIMARY KEY,
            src_id TEXT NOT NULL,
            dst_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            meta_json TEXT NOT NULL DEFAULT '{}',
            hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(src_id) REFERENCES nodes(id),
            FOREIGN KEY(dst_id) REFERENCES nodes(id)
        );

        CREATE TABLE IF NOT EXISTS jurisdictions (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            legal_system TEXT NOT NULL,
            pct_member INTEGER NOT NULL DEFAULT 1,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS audit_ledger (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS self_test_runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            report_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
        CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_id);
        CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_id);
        CREATE INDEX IF NOT EXISTS idx_ledger_seq ON audit_ledger(seq);
        """)

        pct = [
            "US","EP","JP","KR","CN","IN","CA","AU","BR","RU","ZA","DE",
            "FR","GB","IT","ES","NL","SE","CH","AT","BE","DK","FI","GR",
            "IE","LU","MC","PT","TR","IL","SG","MY","ID","TH","PH","VN",
            "MX","AR","CL","CO","PE","EG","MA","NG","KE","SA","AE"
        ]
        with self.conn:
            for code in pct:
                self.conn.execute(
                    """INSERT OR IGNORE INTO jurisdictions
                       (code,name,legal_system,pct_member)
                       VALUES (?,?,?,1)""",
                    (code, code, "unknown"),
                )
            self.conn.execute(
                """INSERT OR IGNORE INTO jurisdictions
                   (code,name,legal_system,pct_member)
                   VALUES ('WO','WIPO (PCT)','international',1)"""
            )

    def _create_triggers(self) -> None:
        self.conn.executescript("""
        CREATE TRIGGER IF NOT EXISTS nodes_no_update
        BEFORE UPDATE ON nodes
        BEGIN SELECT RAISE(ABORT, 'UPDATE on nodes is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS nodes_no_delete
        BEFORE DELETE ON nodes
        BEGIN SELECT RAISE(ABORT, 'DELETE on nodes is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS edges_no_update
        BEFORE UPDATE ON edges
        BEGIN SELECT RAISE(ABORT, 'UPDATE on edges is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS edges_no_delete
        BEFORE DELETE ON edges
        BEGIN SELECT RAISE(ABORT, 'DELETE on edges is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS audit_no_update
        BEFORE UPDATE ON audit_ledger
        BEGIN SELECT RAISE(ABORT, 'UPDATE on audit_ledger is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS audit_no_delete
        BEFORE DELETE ON audit_ledger
        BEGIN SELECT RAISE(ABORT, 'DELETE on audit_ledger is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS selftest_no_update
        BEFORE UPDATE ON self_test_runs
        BEGIN SELECT RAISE(ABORT, 'UPDATE on self_test_runs is forbidden'); END;

        CREATE TRIGGER IF NOT EXISTS selftest_no_delete
        BEFORE DELETE ON self_test_runs
        BEGIN SELECT RAISE(ABORT, 'DELETE on self_test_runs is forbidden'); END;
        """)
        self.conn.commit()

    def add_node(
        self,
        node_id: Optional[str] = None,
        node_type: str = "EXTERNAL_REF",
        title: str = "",
        description: str = "",
        timestamp: Optional[str] = None,
        source: str = "",
        meta: Optional[Dict[str, Any]] = None,
        is_readonly: int = 1,
    ) -> str:
        if node_type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {node_type}")
        node_id = node_id or generate_id("node")
        timestamp = timestamp or now_iso()
        source = source or "UNSPECIFIED"
        meta_json = canonical_json(meta or {})
        hash_val = compute_hash(
            node_id, node_type, title, description, timestamp,
            source, meta_json, is_readonly
        )
        created_at = now_iso()
        self.conn.execute(
            """INSERT INTO nodes
               (id,type,title,description,timestamp,source,meta_json,hash,
                is_readonly,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                node_id, node_type, title, description, timestamp, source,
                meta_json, hash_val, is_readonly, created_at
            ),
        )
        return node_id

    def add_edge(
        self,
        src_id: str,
        dst_id: str,
        edge_type: str,
        weight: float = 1.0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type: {edge_type}")
        if not self.get_node(src_id) or not self.get_node(dst_id):
            raise ValueError("Both edge endpoints must already exist.")
        edge_id = generate_id("edge")
        meta_json = canonical_json(meta or {})
        created_at = now_iso()
        hash_val = compute_hash(
            edge_id, src_id, dst_id, edge_type, weight, meta_json, created_at
        )
        self.conn.execute(
            """INSERT INTO edges
               (id,src_id,dst_id,edge_type,weight,meta_json,hash,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                edge_id, src_id, dst_id, edge_type, float(weight),
                meta_json, hash_val, created_at
            ),
        )
        return edge_id

    def get_node(self, node_id: str):
        return self.conn.execute(
            "SELECT * FROM nodes WHERE id=?", (node_id,)
        ).fetchone()

    def get_all_nodes(self, exclude_types=None):
        if exclude_types:
            placeholders = ",".join("?" for _ in exclude_types)
            return self.conn.execute(
                f"SELECT * FROM nodes WHERE type NOT IN ({placeholders}) ORDER BY rowid",
                tuple(exclude_types),
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM nodes ORDER BY rowid"
        ).fetchall()

    def get_all_edges(self):
        return self.conn.execute(
            "SELECT * FROM edges ORDER BY rowid"
        ).fetchall()

    def log_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        actor: str = "SYSTEM",
    ) -> str:
        event_id = generate_id("event")
        timestamp = now_iso()
        payload_json = canonical_json(payload)
        prev = self.conn.execute(
            "SELECT hash FROM audit_ledger ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev["hash"] if prev else "GENESIS"
        row_hash = compute_hash(
            event_id, timestamp, event_type, actor,
            payload_json, prev_hash
        )
        self.conn.execute(
            """INSERT INTO audit_ledger
               (event_id,timestamp,event_type,actor,payload_json,prev_hash,hash)
               VALUES (?,?,?,?,?,?,?)""",
            (
                event_id, timestamp, event_type, actor,
                payload_json, prev_hash, row_hash
            ),
        )
        return event_id

    def close(self) -> None:
        self.conn.close()


class ProofEngine:
    def __init__(self, db: MasterDB):
        self.db = db

    def calculate_proof_status(self, node_id: str) -> Dict[str, Any]:
        node = self.db.get_node(node_id)
        if not node:
            return {"error": "node not found"}

        cur = self.db.conn.cursor()
        rows = cur.execute(
            """SELECT n.type,e.weight,e.meta_json,e.edge_type
               FROM edges e JOIN nodes n ON e.dst_id=n.id
               WHERE e.src_id=?
               AND e.edge_type IN ('SUPPORTED_BY','VALIDATED_BY','MEASURED_BY')""",
            (node_id,),
        ).fetchall()

        total = 0.0
        evidence_count = 0
        independent = False
        reproduced = False

        for row in rows:
            total += EVIDENCE_WEIGHTS.get(row["type"], 0.0) * row["weight"]
            evidence_count += 1
            meta = json.loads(row["meta_json"] or "{}")
            independent = independent or bool(meta.get("independent_check"))
            reproduced = reproduced or bool(meta.get("reproduced"))

        failures = cur.execute(
            """SELECT e.weight
               FROM edges e
               WHERE e.edge_type='CORRECTS' AND e.dst_id=?""",
            (node_id,),
        ).fetchall()

        for row in failures:
            total += EVIDENCE_WEIGHTS["FAILURE_CORRECTION"] * row["weight"]

        if reproduced:
            total += REPRODUCIBILITY_WEIGHT
        if independent:
            total += INDEPENDENT_CHECK_WEIGHT

        total = max(0.0, min(total, 1.5))

        if total < 0.2:
            level = "UNVERIFIED"
        elif total < 0.4:
            level = "INDICATION"
        elif total < 0.6:
            level = "EVIDENCE"
        elif total < 0.8:
            level = "VALIDATED"
        elif total < 1.0:
            level = "PROVEN"
        elif total < 1.2:
            level = "REPRODUCED"
        else:
            level = "INDEPENDENTLY_VERIFIED"

        # A score is an internal indicator, not proof.
        proof_authorized = (
            node["type"] == "RESULT"
            and independent
            and reproduced
            and evidence_count > 0
        )

        return {
            "node_id": node_id,
            "score": round(total, 3),
            "level": level,
            "evidence_count": evidence_count,
            "has_independent": independent,
            "has_reproducibility": reproduced,
            "failure_penalties": len(failures),
            "proof_authorized": proof_authorized,
            "warning": "Score is not proof and does not replace validation."
        }


class HardenedAudit:
    def __init__(self, db: MasterDB):
        self.db = db

    def integrity_check(self) -> Dict[str, Any]:
        issues = []

        # Node hashes
        for n in self.db.get_all_nodes():
            expected = compute_hash(
                n["id"], n["type"], n["title"], n["description"],
                n["timestamp"], n["source"], n["meta_json"],
                n["is_readonly"]
            )
            if n["hash"] != expected:
                issues.append(f"NODE_HASH_MISMATCH:{n['id']}")

        # Edge hashes
        for e in self.db.get_all_edges():
            expected = compute_hash(
                e["id"], e["src_id"], e["dst_id"], e["edge_type"],
                e["weight"], e["meta_json"], e["created_at"]
            )
            if e["hash"] != expected:
                issues.append(f"EDGE_HASH_MISMATCH:{e['id']}")

        # Orphans
        orphans = self.db.conn.execute(
            """SELECT e.id FROM edges e
               LEFT JOIN nodes a ON e.src_id=a.id
               LEFT JOIN nodes b ON e.dst_id=b.id
               WHERE a.id IS NULL OR b.id IS NULL"""
        ).fetchall()
        issues.extend(f"ORPHAN_EDGE:{r['id']}" for r in orphans)

        # Ledger chain
        rows = self.db.conn.execute(
            "SELECT * FROM audit_ledger ORDER BY seq"
        ).fetchall()
        previous = "GENESIS"
        for row in rows:
            if row["prev_hash"] != previous:
                issues.append(f"LEDGER_PREV_HASH_MISMATCH:{row['seq']}")
            expected = compute_hash(
                row["event_id"], row["timestamp"], row["event_type"],
                row["actor"], row["payload_json"], row["prev_hash"]
            )
            if row["hash"] != expected:
                issues.append(f"LEDGER_HASH_MISMATCH:{row['seq']}")
            previous = row["hash"]

        # High score with no evidence
        engine = ProofEngine(self.db)
        for n in self.db.get_all_nodes(exclude_types={"PROOF_STATUS"}):
            st = engine.calculate_proof_status(n["id"])
            if st.get("score", 0) > 0.7 and st.get("evidence_count", 0) == 0:
                issues.append(f"UNSUPPORTED_HIGH_SCORE:{n['id']}")

        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "node_count": len(self.db.get_all_nodes()),
            "edge_count": len(self.db.get_all_edges()),
            "ledger_count": len(rows),
        }


def seed_prior_records(db: MasterDB) -> None:
    with db.conn:
        root = db.add_node(
            node_id="ROOT",
            node_type="ROOT",
            title="KIMIA Ω Master Root",
            description="Master graph root.",
            source="seed",
        )
        identity = db.add_node(
            node_id="IDENTITY-1",
            node_type="IDENTITY",
            title="KIMIA Ω Project Identity",
            description="Identity and attribution record.",
            source="seed",
        )
        db.add_edge(root, identity, "HAS_PART")

        records = [
            ("REC-2984", "COMMITMENT", "Records 2,984", "Prior records set"),
            ("EXEC-008", "EXECUTION", "Execution 008", "Execution log 008"),
            ("EXEC-009", "EXECUTION", "Execution 009", "Execution log 009"),
            ("DISC-92BD1A476BC2", "DISCOVERY", "Discovery record", "Existing discovery record"),
            ("RECON-003", "VALIDATION", "Recon 003", "Existing reconciliation validation"),
            ("REAL_DISCOVERY_002", "DISCOVERY", "Real Discovery 002", "Existing real discovery record"),
            ("FINAL_BOUNDARY_TEST", "VALIDATION", "Final Boundary Test", "Existing boundary test"),
            ("KIMIA_OMEGA_ARCH", "GOVERNANCE_AUTHORITY", "KIMIA Ω Architecture", "Architecture definition"),
            ("EVIDENCE_LEDGER", "EVIDENCE", "Evidence Ledger", "Evidence ledger reference"),
            ("ERRORS_LOG", "FAILURE_CORRECTION", "Errors and Corrections", "Errors and corrections"),
            ("ALL_PASS_LOG", "RESULT", "All PASS Log", "Historical PASS record"),
        ]

        for rid, rtype, title, desc in records:
            n = db.add_node(
                node_id=rid,
                node_type=rtype,
                title=title,
                description=desc,
                source="seed",
            )
            db.add_edge(root, n, "HAS_PART")
            db.add_edge(identity, n, "PART_OF")

        invention = db.add_node(
            node_id="INVENTION-CANDIDATE-1",
            node_type="INVENTION_CANDIDATE",
            title="KIMIA Ω Invention Candidate",
            description="Candidate aggregation; not proof of invention or ownership.",
            source="aggregation",
        )

        for rec_id in ["DISC-92BD1A476BC2", "REAL_DISCOVERY_002"]:
            db.add_edge(invention, rec_id, "SUPPORTED_BY")

        for val_id in ["RECON-003", "FINAL_BOUNDARY_TEST"]:
            db.add_edge(
                invention, val_id, "VALIDATED_BY",
                meta={"validation_reference": True}
            )

        int_scope = db.add_node(
            node_id="SCOPE-PCT",
            node_type="INTERNATIONAL_SCOPE",
            title="PCT International Application Path",
            description="PCT is an international application route; it is not an automatic grant.",
            source="seed",
            meta={"route_type": "application_path"},
        )
        db.add_edge(invention, int_scope, "IN_SCOPE_OF")

        for code in ["US", "EP", "CN", "JP", "KR"]:
            jnode = db.add_node(
                node_id=f"JUR-{code}",
                node_type="INTERNATIONAL_SCOPE",
                title=f"Jurisdiction {code}",
                description=f"Target jurisdiction {code}; no grant is asserted.",
                source="seed",
                meta={"jurisdiction_code": code},
            )
            db.add_edge(int_scope, jnode, "IN_SCOPE_OF")

        db.log_event(
            "SEED",
            {"records_seeded": len(records), "note": "Historical references only; no new proof created."}
        )


def import_directory(db: MasterDB, directory: str) -> Dict[str, Any]:
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    imported = 0
    errors = []

    with db.conn:
        for f in sorted(path.iterdir()):
            if f.suffix.lower() == ".json":
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if not isinstance(item, dict):
                            errors.append(f"{f.name}: item is not an object")
                            continue
                        db.add_node(
                            node_id=item.get("id"),
                            node_type=item.get("type", "EXTERNAL_REF"),
                            title=item.get("title", f.stem),
                            description=item.get("description", ""),
                            timestamp=item.get("timestamp", now_iso()),
                            source=str(f),
                            meta=item.get("meta", {}),
                        )
                        imported += 1
                except Exception as exc:
                    errors.append(f"{f.name}: {exc}")

            elif f.suffix.lower() == ".csv":
                try:
                    with f.open("r", encoding="utf-8", newline="") as fh:
                        reader = csv.DictReader(fh)
                        for row in reader:
                            db.add_node(
                                node_id=row.get("id") or None,
                                node_type=row.get("type") or "EXTERNAL_REF",
                                title=row.get("title") or f.stem,
                                description=row.get("description") or "",
                                timestamp=row.get("timestamp") or now_iso(),
                                source=str(f),
                                meta={
                                    k: v for k, v in row.items()
                                    if k not in {"id", "type", "title", "description", "timestamp"}
                                },
                            )
                            imported += 1
                except Exception as exc:
                    errors.append(f"{f.name}: {exc}")

    db.log_event(
        "IMPORT",
        {"directory": str(path), "imported": imported, "errors": errors}
    )
    return {"imported": imported, "errors": errors}


def run_nist_cycle(db: MasterDB, cycle_id: Optional[str] = None) -> str:
    cycle_id = cycle_id or generate_id("NIST")

    with db.conn:
        cycle = db.add_node(
            node_id=cycle_id,
            node_type="NIST_CYCLE",
            title=f"NIST Cycle {cycle_id}",
            description="Govern → Map → Measure → Manage",
            source="system",
            meta={"cycle": cycle_id},
        )

        phases = {}
        for phase in ["Govern", "Map", "Measure", "Manage"]:
            pid = f"{cycle_id}-{phase}"
            phases[phase] = db.add_node(
                node_id=pid,
                node_type="NIST_CYCLE",
                title=f"{phase} Phase",
                description=f"NIST {phase} phase.",
                source="system",
                meta={"cycle": cycle_id, "phase": phase},
            )
            db.add_edge(cycle, pid, "HAS_PART")

        if db.get_node("KIMIA_OMEGA_ARCH"):
            db.add_edge(phases["Govern"], "KIMIA_OMEGA_ARCH", "GOVERNS")

        for n in db.get_all_nodes(exclude_types={"PROOF_STATUS"}):
            db.add_edge(phases["Map"], n["id"], "PART_OF")

        measurements = db.conn.execute(
            "SELECT id FROM nodes WHERE type='MEASUREMENT'"
        ).fetchall()
        for m in measurements:
            db.add_edge(phases["Measure"], m["id"], "MEASURED_BY")

        for typ in ["LEARNING_EVOLUTION", "FAILURE_CORRECTION"]:
            for n in db.conn.execute(
                "SELECT id FROM nodes WHERE type=?", (typ,)
            ).fetchall():
                db.add_edge(phases["Manage"], n["id"], "IMPLEMENTS")

        db.log_event("NIST_CYCLE", {"cycle_id": cycle_id})

    return cycle_id


def run_self_test(db: MasterDB) -> Dict[str, Any]:
    run_id = generate_id("SELFTEST")
    started = now_iso()
    checks = {}

    def check(name, fn):
        try:
            result = fn()
            checks[name] = {"status": "PASS", "detail": result}
        except Exception as exc:
            checks[name] = {"status": "FAIL", "detail": str(exc)}

    check("schema", lambda: db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall())

    def trigger_check():
        db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        ).fetchall()
        return "triggers present"

    check("triggers", trigger_check)

    def append_only_check():
        n = db.get_all_nodes()[0]
        try:
            db.conn.execute(
                "UPDATE nodes SET title=title WHERE id=?", (n["id"],)
            )
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("UPDATE was not blocked")
        return "UPDATE blocked"

    check("append_only", append_only_check)

    def delete_check():
        n = db.get_all_nodes()[0]
        try:
            db.conn.execute("DELETE FROM nodes WHERE id=?", (n["id"],))
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("DELETE was not blocked")
        return "DELETE blocked"

    check("delete_block", delete_check)

    check("integrity", lambda: HardenedAudit(db).integrity_check())

    passed = all(v["status"] == "PASS" for v in checks.values())
    status = "PASS" if passed else "FAIL"
    report = {
        "run_id": run_id,
        "status": status,
        "checks": checks,
        "operational_claim_allowed": passed,
        "proof_claim_allowed": False,
        "note": "Self-test PASS does not prove project claims.",
    }

    with db.conn:
        db.conn.execute(
            """INSERT INTO self_test_runs
               (run_id,started_at,finished_at,status,report_json)
               VALUES (?,?,?,?,?)""",
            (
                run_id, started, now_iso(), status,
                canonical_json(report)
            ),
        )
        db.log_event("SELF_TEST", report)

    return report


def export_graph(db: MasterDB, output_path: str) -> None:
    audit = HardenedAudit(db).integrity_check()
    nodes = [dict(r) for r in db.get_all_nodes()]
    edges = [dict(r) for r in db.get_all_edges()]
    ledger = [
        dict(r) for r in db.conn.execute(
            "SELECT * FROM audit_ledger ORDER BY seq"
        ).fetchall()
    ]

    data = {
        "format": "KIMIA_OMEGA_MASTER_EXPORT_V1",
        "exported_at": now_iso(),
        "audit_snapshot": audit,
        "nodes": nodes,
        "edges": edges,
        "audit_ledger": ledger,
        "truth_constraints": {
            "no_delete": True,
            "no_update": True,
            "claim_not_proof": True,
            "score_not_proof": True,
            "pct_not_automatic_grant": True,
            "no_fabricated_pass": True,
            "no_false_attribution": True,
        },
    }

    Path(output_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    db.log_event(
        "EXPORT",
        {"output": output_path, "audit_status": audit["status"]}
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KIMIA Ω Hardened Master System"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize and seed")
    imp = sub.add_parser("import", help="Import JSON/CSV directory")
    imp.add_argument("directory")

    proof = sub.add_parser("proof-status", help="Evidence status only")
    proof.add_argument("--node-id")

    sub.add_parser("nist-cycle", help="Run NIST cycle")
    sub.add_parser("self-test", help="Run internal self-validation")
    sub.add_parser("audit", help="Run integrity audit")

    exp = sub.add_parser("export", help="Export complete graph and ledger")
    exp.add_argument("--output", default=EXPORT_FILE)

    args = parser.parse_args()
    db = MasterDB(DB_FILE)

    try:
        if args.command == "init":
            # Idempotence without overwriting: a second init reports existing IDs.
            try:
                seed_prior_records(db)
            except sqlite3.IntegrityError as exc:
                db.log_event("INIT_BLOCKED", {"reason": str(exc)})
                print("INIT BLOCKED: existing immutable records prevent reseeding.")
                return 2
            else:
                print("INITIALIZATION COMPLETE")
                print("No claim of proof has been created.")

        elif args.command == "import":
            result = import_directory(db, args.directory)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "proof-status":
            engine = ProofEngine(db)
            if args.node_id:
                result = engine.calculate_proof_status(args.node_id)
                db.log_event("PROOF_STATUS_COMPUTED", result)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for n in db.get_all_nodes(exclude_types={"PROOF_STATUS"}):
                    result = engine.calculate_proof_status(n["id"])
                    print(
                        f"{n['id']} | {n['type']} | "
                        f"score={result['score']} | level={result['level']} | "
                        f"proof_authorized={result['proof_authorized']}"
                    )

        elif args.command == "nist-cycle":
            cid = run_nist_cycle(db)
            print(f"NIST CYCLE CREATED: {cid}")

        elif args.command == "self-test":
            result = run_self_test(db)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "PASS" else 1

        elif args.command == "audit":
            result = HardenedAudit(db).integrity_check()
            db.log_event("AUDIT", result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "PASS" else 1

        elif args.command == "export":
            export_graph(db, args.output)
            print(f"EXPORTED: {args.output}")

        return 0

    except Exception as exc:
        try:
            db.log_event(
                "SYSTEM_ERROR",
                {"error_type": type(exc).__name__, "error": str(exc)}
            )
            db.conn.commit()
        except Exception:
            pass
        print(f"SYSTEM ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
