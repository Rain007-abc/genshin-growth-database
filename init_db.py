"""Build the self-contained SQLite database using the bundled offline JSON."""

import json
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "genshin_growth.db"
SNAPSHOT_PATH = ROOT / "data" / "source_snapshot.json"


def build_database(db_path=DB_PATH, snapshot_path=SNAPSHOT_PATH):
    payload = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Do not overwrite a user's inventory: rebuilding requires a fresh target.
    if db_path.exists():
        raise FileExistsError(f"Database already exists: {db_path}. Use a different output path.")

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
            with conn:
                conn.executemany(
                    "INSERT INTO materials(id,name_zh,name_en,category,farm_days,farm_hint) VALUES (?,?,?,?,?,?)",
                    [(m["id"],m["name_zh"],m["name_en"],m["category"],m["farm_days"],m["farm_hint"]) for m in payload["materials"]],
                )
                for c in payload["characters"]:
                    conn.execute(
                        "INSERT INTO characters VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (c["id"],c["slug"],c["name_zh"],c["name_en"],c["element"],c["weapon"],c["region"],c["rarity"],
                         c["normal_attack"],c["elemental_skill"],c["elemental_burst"]),
                    )
                    for phase in c["ascension"]:
                        conn.executemany(
                            "INSERT INTO ascension_requirements VALUES (?,?,?,?)",
                            [(c["id"],phase["step"],v["material_id"],v["quantity"]) for v in phase["costs"]],
                        )
                    for step in c["talent"]:
                        conn.executemany(
                            "INSERT INTO talent_requirements VALUES (?,?,?,?)",
                            [(c["id"],step["step"],v["material_id"],v["quantity"]) for v in step["costs"]],
                        )
                conn.execute(
                    "INSERT INTO data_sources VALUES (?,?,?,?)",
                    ("genshin-db",payload["source_repository"],payload["source_commit"],payload["license"]),
                )
                # Illustrative backpack quantities only; not the user's game account.
                example_stocks = {202: 350000, 100027: 25, 113011: 4, 112002: 16, 104313: 5}
                conn.executemany(
                    "INSERT INTO inventory VALUES (?,?)",
                    [(mid,n) for mid,n in example_stocks.items() if conn.execute("SELECT 1 FROM materials WHERE id=?",(mid,)).fetchone()],
                )
            errors = conn.execute("PRAGMA foreign_key_check").fetchall()
            if errors:
                raise RuntimeError(f"Foreign key integrity check failed: {errors[:4]}")
        return {"characters":len(payload["characters"]), "materials":len(payload["materials"]), "path":str(db_path)}
    except Exception:
        db_path.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    print(build_database())
