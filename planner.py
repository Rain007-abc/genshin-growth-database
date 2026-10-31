"""Database queries and resource shortage calculation."""

from collections import defaultdict
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "genshin_growth.db"
CATEGORY_ORDER = ["地区特产", "世界首领", "天赋书", "周本材料", "敌人掉落", "元素宝石", "智识之冕", "货币", "其他"]
TALENT_CAPS = {0: 1, 1: 1, 2: 2, 3: 4, 4: 6, 5: 8, 6: 10}


def get_connection(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def list_characters(conn):
    return [dict(row) for row in conn.execute(
        "SELECT id,slug,name_zh,name_en,element,weapon,region,rarity,normal_attack,elemental_skill,elemental_burst "
        "FROM characters ORDER BY name_zh COLLATE NOCASE"
    )]


def _require_range(label, low, high, from_value, to_value):
    if not (low <= from_value <= high and low <= to_value <= high):
        raise ValueError(f"{label}必须在 {low}–{high} 之间")
    if to_value < from_value:
        raise ValueError(f"{label}目标不能低于当前进度")


def calculate_plan(conn, character_id, from_phase=0, to_phase=6, talents=None):
    """Aggregate real character costs, then subtract a shared player's inventory.

    Talents are independent normal/skill/burst tracks. Their common recipe is
    added once for each track, preventing undercounting shared resources.
    """
    talents = talents or {"attack": (1, 1), "skill": (1, 6), "burst": (1, 8)}
    _require_range("突破阶段", 0, 6, from_phase, to_phase)
    for label in ("attack", "skill", "burst"):
        if label not in talents:
            raise ValueError(f"缺少 {label} 天赋等级")
        _require_range(f"{label}天赋", 1, 10, *talents[label])

    character = conn.execute("SELECT * FROM characters WHERE id=?", (character_id,)).fetchone()
    if character is None:
        raise ValueError("角色不存在")

    quantities = defaultdict(int)
    breakdowns = defaultdict(lambda: defaultdict(int))
    asc_rows = conn.execute(
        "SELECT material_id, quantity FROM ascension_requirements "
        "WHERE character_id=? AND phase>? AND phase<=?",
        (character_id, from_phase, to_phase),
    )
    for row in asc_rows:
        quantities[row["material_id"]] += row["quantity"]
        breakdowns[row["material_id"]]["突破"] += row["quantity"]

    for label, (current, target) in talents.items():
        rows = conn.execute(
            "SELECT material_id,quantity FROM talent_requirements "
            "WHERE character_id=? AND to_level>? AND to_level<=?",
            (character_id, current, target),
        )
        for row in rows:
            quantities[row["material_id"]] += row["quantity"]
            breakdowns[row["material_id"]][label] += row["quantity"]

    material_rows = conn.execute(
        "SELECT m.*,COALESCE(i.quantity,0) AS owned FROM materials m "
        "LEFT JOIN inventory i ON i.material_id=m.id WHERE m.id IN ({})".format(
            ",".join("?" for _ in quantities) or "NULL"
        ), tuple(quantities),
    )
    output = []
    for row in material_rows:
        needed = quantities[row["id"]]
        owned = row["owned"]
        output.append({
            "id": row["id"], "name_zh": row["name_zh"], "name_en": row["name_en"],
            "category": row["category"], "farm_days": row["farm_days"],
            "farm_hint": row["farm_hint"], "required": needed, "owned": owned,
            "missing": max(0, needed - owned), "breakdown": dict(breakdowns[row["id"]]),
        })
    output.sort(key=lambda x: (CATEGORY_ORDER.index(x["category"]) if x["category"] in CATEGORY_ORDER else 99,
                               x["missing"] == 0, -x["missing"], x["name_zh"]))
    warnings = []
    cap = TALENT_CAPS[to_phase]
    if any(target > cap for _, target in talents.values()):
        warnings.append(f"目标突破阶段 {to_phase} 对应天赋等级上限约为 {cap}；若要完成更高天赋，请提高突破阶段。")

    return {
        "character": dict(character),
        "selection": {"from_phase":from_phase,"to_phase":to_phase,"talents":talents},
        "material_count": len(output),
        "shortage_count": sum(item["missing"] > 0 for item in output),
        "materials": output, "warnings": warnings,
        "notes": ["数量按突破阶段及三个天赋逐级累加；不包含角色经验书、武器、圣遗物。",
                  "背包数值是示例/手动录入，不与游戏账号连接；掉落存在随机性，不提供树脂最优解。"],
    }


def set_inventory(conn, material_id, quantity):
    if type(quantity) is not int or quantity < 0 or quantity > 999999999:
        raise ValueError("背包数量必须是 0 到 999999999 的整数")
    if type(material_id) is not int or not conn.execute("SELECT 1 FROM materials WHERE id=?", (material_id,)).fetchone():
        raise ValueError("材料不存在")
    with conn:
        conn.execute(
            "INSERT INTO inventory(material_id,quantity) VALUES(?,?) "
            "ON CONFLICT(material_id) DO UPDATE SET quantity=excluded.quantity",
            (material_id, quantity),
        )
    return quantity
