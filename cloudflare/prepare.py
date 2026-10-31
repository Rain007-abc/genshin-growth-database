"""Generate allowlisted assets and deterministic, inventory-free D1 migration."""
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "cloudflare"

def prepare():
    snapshot = json.loads((ROOT / "data/source_snapshot.json").read_text(encoding="utf-8"))
    schema = (ROOT / "schema.sql").read_text(encoding="utf-8")
    # Keep the original schema unchanged, including an always-empty inventory table.
    with sqlite3.connect(":memory:") as db:
        db.executescript(schema)
        for m in snapshot["materials"]:
            db.execute("INSERT INTO materials VALUES (?,?,?,?,?,?)", tuple(m[k] for k in
                       ("id", "name_zh", "name_en", "category", "farm_days", "farm_hint")))
        for c in snapshot["characters"]:
            db.execute("INSERT INTO characters VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(c[k] for k in
                       ("id", "slug", "name_zh", "name_en", "element", "weapon", "region", "rarity", "normal_attack", "elemental_skill", "elemental_burst")))
            for key, table in [("ascension", "ascension_requirements"), ("talent", "talent_requirements")]:
                for step in c[key]:
                    db.executemany(f"INSERT INTO {table} VALUES (?,?,?,?)",
                                   [(c["id"], step["step"], v["material_id"], v["quantity"]) for v in step["costs"]])
        db.execute("INSERT INTO data_sources VALUES (?,?,?,?)", ("genshin-db", snapshot["source_repository"], snapshot["source_commit"], snapshot["license"]))
        counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
                  ("characters", "materials", "ascension_requirements", "talent_requirements", "inventory", "data_sources")}
        assert counts["characters"] == 120 and counts["materials"] == 309 and counts["inventory"] == 0
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        # Plain CREATE/INSERT: duplicate/manual reimport fails, never hides conflicts.
        sql = schema.replace("IF NOT EXISTS ", "") + "\n"
        for table in counts:
            if table == "inventory":
                continue
            for row in db.execute(f"SELECT * FROM {table} ORDER BY 1,2"):
                values = ",".join("NULL" if v is None else str(v) if isinstance(v, int) else "'" + v.replace("'", "''") + "'" for v in row)
                sql += f"INSERT INTO {table} VALUES ({values});\n"
    migrations = HERE / "migrations"
    migrations.mkdir(exist_ok=True)
    migration = migrations / "0001_standard_data.sql"
    # An applied migration must never silently change when the snapshot changes.
    if migration.exists() and migration.read_text(encoding="utf-8") != sql:
        raise RuntimeError("Migration differs: create an explicitly reviewed new migration instead")
    migration.write_text(sql, encoding="utf-8", newline="\n")
    public = HERE / "public"
    public.mkdir(exist_ok=True)
    assets = {"index.html": (ROOT / "static/index.html").read_text(encoding="utf-8")
              .replace("SQLite · 离线可用", "D1 · 浏览器独立库存")
              .replace("所有数据保存在本机 SQLite 数据库。", "库存仅保存在当前浏览器 localStorage，不跨浏览器或设备同步；清除网站数据会丢失库存。游戏图片未分发，使用占位图。"),
              "style.css": (ROOT / "static/style.css").read_text(encoding="utf-8"),
              "app.js": "import { cloudApi } from '/inventory.js';\nconst api = cloudApi(networkApi);\n" +
              (ROOT / "static/app.js").read_text(encoding="utf-8").replace("async function api(", "async function networkApi("),
              "inventory.js": (HERE / "inventory.js").read_text(encoding="utf-8"),
              "plan.js": (HERE / "plan.js").read_text(encoding="utf-8"),
              "images/characters/placeholder.svg": (ROOT / "static/images/characters/placeholder.svg").read_text(encoding="utf-8"),
              "images/characters/manifest.json": json.dumps({"characters": {}})}
    assets["index.html"] = assets["index.html"].replace('<script src="/app.js" defer>', '<script src="/app.js" type="module">')
    # Fail closed if a previous build contains unexpected resources; never delete local files.
    unexpected = {p.relative_to(public).as_posix() for p in public.rglob("*") if p.is_file()} - assets.keys()
    if unexpected:
        raise RuntimeError(f"Unexpected assets: {unexpected}. Inspect manually before building.")
    for name, content in assets.items():
        dest = public / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps(counts))
    return counts

if __name__ == "__main__":
    prepare()
