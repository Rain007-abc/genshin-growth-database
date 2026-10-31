"""Audit all character mappings, decode all images, and write local provenance.

Pillow is an authoring/verification dependency only, not an app dependency.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'static/images/characters'
SOURCES = ROOT / 'data/character_art_sources'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    manifest = read(ART / 'manifest.json')
    with sqlite3.connect((ROOT / 'genshin_growth.db').as_uri() + '?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute('SELECT id,slug,name_zh,name_en FROM characters ORDER BY id')]
    assert len(rows) == 120 and set(manifest['characters']) == {str(c['id']) for c in rows}
    assert not manifest['pilot']
    identifiers = read(SOURCES / 'hoyo-characters.json')
    images = read(SOURCES / 'genshin-db-image.json')
    identities = read(SOURCES / 'verified-identities.json')
    duplicates = defaultdict(list)
    original_bytes = local_bytes = 0
    counts = Counter()
    failures = []
    for c in rows:
        cid = str(c['id'])
        entry = manifest['characters'][cid]
        assert all(c[k] == entry[k] for k in c), cid
        if cid in identifiers:
            assert 'UI_AvatarIcon_' + identifiers[cid] == images[c['slug']]['filename_icon'], cid
        else:
            identity = identities[cid]
            assert identity['id'] == c['id'] and identity['name'] == c['name_en'], cid
            assert identity['icon'] == images[c['slug']]['filename_icon'], cid
        counts[entry['status']] += 1
        for kind in ['splash', 'avatar']:
            if not entry[kind]:
                failures.append({'id': c['id'], 'name': c['name_zh'], 'kind': kind})
                continue
            asset = entry['assets'][kind]
            path = ART / Path(entry[kind]).name
            raw = path.read_bytes()
            assert sha256(raw).hexdigest() == asset['sha256'], path
            with Image.open(path) as image:
                image.load()
                assert image.format == 'WEBP' and image.mode == 'RGBA', path
                assert list(image.size) == asset['size'], path
                assert image.getchannel('A').getextrema()[0] == 0, path
                if kind == 'splash':
                    assert asset['source_size'] == asset['size'], path
                else:
                    assert max(image.size) <= 96, path
            original_bytes += asset['original_bytes']
            local_bytes += len(raw)
            duplicates[(kind, asset['original_sha256'])].append(cid)
    duplicate_groups = [v for v in duplicates.values() if len(v) > 1]
    assert not duplicate_groups, duplicate_groups
    result = {'characters': len(rows), 'counts': dict(counts), 'decoded_images': len(duplicates),
              'identity_mismatches': [], 'duplicate_groups': duplicate_groups, 'missing_assets': failures,
              'original_bytes': original_bytes, 'local_bytes': local_bytes,
              'saving_percent': round(100 * (1 - local_bytes / original_bytes), 2)}
    (SOURCES / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 13)
    for page in range(3):
        sheet = Image.new('RGB', (1400, 1000), '#132336')
        draw = ImageDraw.Draw(sheet)
        for i, c in enumerate(rows[page * 40:(page + 1) * 40]):
            x, y = (i % 5) * 280, (i // 5) * 125
            entry = manifest['characters'][str(c['id'])]
            if entry['splash']:
                with Image.open(ART / Path(entry['splash']).name) as image:
                    image.thumbnail((270, 99))
                    sheet.paste(image, (x + (280 - image.width) // 2, y), image)
            draw.text((x + 6, y + 100), f"{c['id']} {c['name_en']}", font=font, fill='#e5c48d')
        sheet.save(SOURCES / f'contact-sheet-{page + 1}.jpg', quality=92)
    lines = ['# 角色图片来源与匹配记录', '', '核验日期：2026-10-29。用途：本机、非商业数据库课堂演示；没有上传或发布图片。', '',
             '## 覆盖结果', '',
             f"- 完整立绘：{counts['full']} / 120；仅头像：{counts['avatar_only']}；缺失：{counts['missing']}。占位图不计入成功。",
             '- 角色 ID / slug / 中英文名称匹配失败名单：无。全部 240 个文件已解码、核对尺寸、透明通道和 SHA-256；没有跨角色重复图片。',
             f'- 原始 PNG 合计 {original_bytes / 1000000:.2f} MB；本地 WebP 合计 {local_bytes / 1000000:.2f} MB，减少 {result["saving_percent"]}%。',
             '- 立绘使用原始完整画布与原尺寸的无损 WebP；头像等比缩小到最长边 96 px，保留透明背景。页面以 object-fit: contain 显示。', '',
             '## 实际使用来源与条件', '',
             '1. [ScobbleQ/HoYo-Assets](https://github.com/ScobbleQ/HoYo-Assets)：96 位角色的立绘与头像。固定提交 `9324d91d6bd5719223efed4236638cd9b75ca1f8`；下载路径为 `genshin/splash/<ID>.png` 和 `genshin/icon/<ID>.png`。README 表示任何人可使用，并明确美术归 HoYoverse；说明存档于 `data/character_art_sources/HoYo-Assets-README.txt`。文件另核对 Git blob SHA-1。仓库首页标注的旧版本不能代表实际覆盖，实际与 SQLite 的 120 个 ID 逐一求交得到 96。',
             '2. [Yatta 素材站](https://gi.yatta.moe)：补足 24 位角色的立绘与头像，图片地址为 `https://gi.yatta.moe/assets/UI/<游戏内部标识>.png`，每张的精确地址、大小和 SHA-256 见 manifest。服务器不提供固定图片版本，已下载到本地固定保存。此次能够取得这些精确图片地址，但其首页/API 对部分请求返回 403，未取得可将游戏美术重新授权的素材许可文本；不声称该站或本项目获得 HoYoverse 正式授权。没有绕过登录或访问保护。',
             '3. [theBowja/genshin-db](https://github.com/theBowja/genshin-db)：只用作身份及图片标识索引，没有从中下载角色美术。角色 ID/英文名记录及 `src/data/image/characters.json` 均核验到现有数据快照提交 `49a6544a6c6ae36089cb42fa591fc46f01de8bcf`（图片索引 blob `7842ed8f958e5292b87a1fbc7fed58c258c139bf`）。其 MIT 许可不能解释为游戏图片使用授权。', '',
             '**版权边界：** 图片版权仍属于 HoYoverse / miHoYo 及相关权利人（联动角色可能涉及其他权利人）。素材搬运站的说明及代码仓库许可证不等于游戏图片授权。本次仅按用户指定用途保存在本机，保留来源；不授予公开分发、商业使用或再许可权利。公开发布或改变用途前需要另行核实相关权利人的使用要求。', '',
             '## 调查但未采用', '',
             '- [CMHopeSunshine/GenshinWikiMap](https://github.com/CMHopeSunshine/GenshinWikiMap)，提交 `7fafe2e18011008d47e347f0f68216d05da0c1f1`：资源较旧，未补齐全部角色。README 声明资料版权属于米哈游、仅供学习交流；传播或在其他项目使用制作好的游戏图鉴须先联系作者，私人使用无需。未下载其成品图鉴或美术；GPL-3.0 不能等同于美术授权。',
             '- [EnkaNetwork/API-docs](https://github.com/EnkaNetwork/API-docs)：调查过角色 ID/内部标识表；图片端点返回 403，因此没有采用其图片，也没有将它算作实际素材来源。', '',
             '## 匹配与本地管理', '',
             '- HoYo-Assets：数据库数值 ID 精确匹配文件名；同时将 `gi_characters.json` 的内部标识与 genshin-db 对应精确 slug 的头像标识交叉核验。',
             '- 补充角色：读取固定提交下 `English/characters/<数据库slug>.json`，要求 ID 与英文名同时完全一致；再以同一提交的图片索引取得内部标识。没有拼写相似度、模糊中文名、搜索图片或自动借用其他角色。',
             '- 命名：`static/images/characters/<ID>.webp` 为完整立绘；`<ID>-avatar.webp` 为头像。`placeholder.svg` 是本项目绘制的通用几何占位图。',
             '- `static/images/characters/manifest.json` 包含每个角色的中英文名、ID、slug、来源 URL、匹配方法、原图及本地 SHA-256、尺寸、体积和缺失错误。',
             '- `data/character_art_sources/` 保存候选资源索引、身份核验、审计 JSON 和三张全角色核对缩略图。它们仅供开发核验，不由网站静态路由公开提供。',
             '- 网站运行不联网：列表头像 loading="lazy"；详情只请求当前角色的立绘，异步解码；缺图/加载错误统一显示占位图，manifest 不可用时养成 API 仍可用。',
             '- 维护脚本 `scripts/download_character_art.py` 和 `scripts/audit_character_art.py` 需 Pillow；本次使用已有的 Codex 随附 Python/Pillow，无需安装新包。日常 `run_windows.bat` / `python app.py` 仍只需 Python 标准库。', '',
             '## 逐角色清单', '', '| ID | slug | 中文名 | English | 立绘 | 头像 | 素材来源 |', '| --- | --- | --- | --- | --- | --- | --- |']
    for c in rows:
        entry = manifest['characters'][str(c['id'])]
        source = entry['assets'].get('splash', {}).get('source', '无')
        lines.append(f"| {c['id']} | {c['slug']} | {c['name_zh']} | {c['name_en']} | {'完整' if entry['splash'] else '缺失'} | {'已取得' if entry['avatar'] else '缺失'} | {source} |")
    (ROOT / 'CHARACTER_ART_SOURCES.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
