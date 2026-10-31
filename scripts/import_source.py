"""Convert a local genshin-db repository snapshot into an offline, compact JSON.

Run only when refreshing the upstream data, NOT to start the demo application.
This script does not execute any code from the downloaded repository.
"""

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import subprocess


BASE_FOLDER = Path("src/data")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path, help="Local checkout of theBowja/genshin-db")
    parser.add_argument("output", type=Path, help="Output JSON file")
    args = parser.parse_args()
    repo = args.repository.resolve()
    en = repo / BASE_FOLDER / "English"
    zh = repo / BASE_FOLDER / "ChineseSimplified"
    if not (en / "characters").is_dir() or not (zh / "talents").is_dir():
        parser.error("Repository needs English and ChineseSimplified characters/talents data")

    material_names = {}
    material_kinds = defaultdict(set)
    characters = []

    for english_file in sorted((en / "characters").glob("*.json")):
        slug = english_file.stem
        paths = [
            zh / "characters" / english_file.name,
            en / "talents" / english_file.name,
            zh / "talents" / english_file.name,
        ]
        if not all(p.exists() for p in paths):
            continue
        char_en, char_zh, talents_en, talents_zh = (
            read_json(p) for p in [english_file, *paths]
        )
        asc_en, asc_zh = char_en.get("costs", {}), char_zh.get("costs", {})
        tal_en, tal_zh = talents_en.get("costs", {}), talents_zh.get("costs", {})
        # Traveler variants and other exceptional entries lack uniform progression.
        if not all(f"ascend{i}" in asc_en and f"ascend{i}" in asc_zh for i in range(1, 7)):
            continue
        if not all(f"lvl{i}" in tal_en and f"lvl{i}" in tal_zh for i in range(2, 11)):
            continue

        ascension, talent = [], []
        for kind, keys, out in (
            ("ascension", [f"ascend{i}" for i in range(1, 7)], ascension),
            ("talent", [f"lvl{i}" for i in range(2, 11)], talent),
        ):
            costs_en, costs_zh = (asc_en, asc_zh) if kind == "ascension" else (tal_en, tal_zh)
            for step, key in enumerate(keys):
                english = costs_en[key]
                chinese = {int(v["id"]): v for v in costs_zh[key]}
                step_costs = []
                for idx, item in enumerate(english):
                    mid = int(item["id"])
                    qty = int(item["count"])
                    if qty <= 0:
                        continue
                    if mid not in chinese:
                        raise ValueError(f"Missing Chinese material {mid} in {slug}/{key}")
                    material_names[mid] = {"id": mid, "name_en": item["name"], "name_zh": chinese[mid]["name"]}
                    if mid == 202:
                        category = "货币"
                    elif kind == "ascension":
                        if idx == 1:
                            category = "元素宝石"
                        elif idx == len(english) - 1:
                            category = "敌人掉落"
                        elif idx == len(english) - 2:
                            category = "地区特产"
                        else:
                            category = "世界首领"
                    elif idx == 1:
                        category = "天赋书"
                    elif idx == 2:
                        category = "敌人掉落"
                    elif item["name"] == "Crown of Insight":
                        category = "智识之冕"
                    else:
                        category = "周本材料"
                    material_kinds[mid].add(category)
                    step_costs.append({"material_id": mid, "quantity": qty})
                out.append({"step": step + (1 if kind == "ascension" else 2), "costs": step_costs})

        characters.append({
            "id": int(char_en["id"]), "slug": slug,
            "name_zh": char_zh["name"], "name_en": char_en["name"],
            "element": char_zh.get("elementText", ""),
            "weapon": char_zh.get("weaponText", ""),
            "region": char_zh.get("region", "未知"),
            "rarity": char_en.get("rarity", 4),
            "normal_attack": talents_zh.get("combat1", {}).get("name", "普通攻击"),
            "elemental_skill": talents_zh.get("combat2", {}).get("name", "元素战技"),
            "elemental_burst": talents_zh.get("combat3", {}).get("name", "元素爆发"),
            "ascension": ascension, "talent": talent,
        })

    days_by_material = {}
    for path in (en / "talentmaterialtypes").glob("*.json"):
        info = read_json(path)
        for key in ("2starname", "3starname", "4starname"):
            days_by_material[info[key]] = info.get("day", [])

    category_priority = ["货币", "智识之冕", "天赋书", "元素宝石", "世界首领", "地区特产", "周本材料", "敌人掉落"]
    hints = {
        "货币": "地脉之花、任务与活动",
        "智识之冕": "活动及特殊奖励；数量有限",
        "天赋书": "天赋培养秘境；注意开放日期",
        "元素宝石": "对应元素首领、炼金台转化",
        "世界首领": "冒险之证追踪对应世界首领",
        "地区特产": "地区野外采集；可查看提瓦特互动地图",
        "周本材料": "每周首领挑战；注意每周次数",
        "敌人掉落": "击败对应敌人，低级材料可合成",
    }
    day_zh = {"Monday": "周一", "Tuesday": "周二", "Wednesday": "周三", "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"}
    materials = []
    for mid, info in sorted(material_names.items()):
        kinds = material_kinds[mid]
        category = next((k for k in category_priority if k in kinds), "其他")
        farm_days = days_by_material.get(info["name_en"], [])
        materials.append({
            **info, "category": category,
            "farm_days": "、".join(day_zh.get(x, x) for x in farm_days),
            "farm_hint": hints.get(category, "请以游戏内说明为准"),
        })

    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    snapshot = {
        "source_repository": "https://github.com/theBowja/genshin-db",
        "source_commit": revision,
        "snapshot_date": str(date.today()),
        "license": "MIT, (c) 2020 theBowja. See THIRD_PARTY_LICENSE.md.",
        "excluded_special_cases": "Traveler/Manekin variants without the standard progression tables",
        "characters": characters, "materials": materials,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Snapshot: {len(characters)} characters, {len(materials)} materials, {revision[:10]}")


if __name__ == "__main__":
    main()
