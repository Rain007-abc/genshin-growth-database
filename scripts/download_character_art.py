"""One-off artwork import. Requires Pillow only when importing, never at runtime.

Reads SQLite in read-only mode. No database writes and no approximate name matches.
Run --pilot first, visually verify the page, then run without --pilot.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha1, sha256
from io import BytesIO
import json
from pathlib import Path
import sqlite3
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'data/character_art_sources'
OUTPUT = ROOT / 'static/images/characters'
REVISION = '9324d91d6bd5719223efed4236638cd9b75ca1f8'
PILOT = {10000023, 10000025, 10000006, 10000015, 10000022}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fetch(url):
    request = Request(url, headers={'User-Agent': 'GenshinGrowth-Classroom/1.0'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=25) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code < 500 and exc.code != 429:
                raise
            if attempt == 2:
                raise
        except OSError:
            if attempt == 2:
                raise
        time.sleep(attempt + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args()
    with sqlite3.connect((ROOT / 'genshin_growth.db').as_uri() + '?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute('SELECT id,slug,name_zh,name_en,element FROM characters ORDER BY id')]
    index = {x['path']: x for x in read_json(SOURCES / 'HoYo-Assets-index.json')['files']}
    names = read_json(SOURCES / 'hoyo-characters.json')
    image_names = read_json(SOURCES / 'genshin-db-image.json')
    old = read_json(OUTPUT / 'manifest.json') if (OUTPUT / 'manifest.json').exists() else {'characters': {}}
    OUTPUT.mkdir(parents=True, exist_ok=True)

    def process(row):
        cid = str(row['id'])
        if args.pilot and row['id'] not in PILOT:
            return cid, old['characters'].get(cid, {**row, 'status': 'not_processed', 'avatar': None, 'splash': None})
        entry = {**row, 'avatar': None, 'splash': None, 'assets': {}, 'errors': []}
        for kind, folder, key in [('splash', 'splash', 'filename_gachaSplash'), ('avatar', 'icon', 'filename_icon')]:
            upstream_path = f'genshin/{folder}/{cid}.png'
            expected = index.get(upstream_path)
            if expected and cid in names:
                url = f'https://raw.githubusercontent.com/ScobbleQ/HoYo-Assets/{REVISION}/{upstream_path}'
                match = f'characters.id = repository filename; gi_characters.json internal identifier = {names[cid]}'
                source = 'ScobbleQ/HoYo-Assets'
            else:
                # Exact slug comes from the existing ID-keyed character table.
                # A pinned upstream character record must confirm both ID and name.
                meta = image_names.get(row['slug'], {})
                identity_path = SOURCES / 'verified-identities.json'
                identities = read_json(identity_path) if identity_path.exists() else {}
                identity = identities.get(cid, {})
                if identity.get('id') != row['id'] or identity.get('name') != row['name_en'] or not meta.get(key):
                    entry['errors'].append(f'{kind}: no verified ID metadata')
                    continue
                if identity.get('icon') != meta.get('filename_icon'):
                    entry['errors'].append(f'{kind}: internal identifier mismatch')
                    continue
                url = f'https://gi.yatta.moe/assets/UI/{meta[key]}.png'
                match = 'DB id + exact English name = pinned genshin-db character record; exact slug -> verified internal image identifier'
                source = 'Yatta (Project Amber successor)'
            destination = OUTPUT / (cid + ('.webp' if kind == 'splash' else '-avatar.webp'))
            previous = old['characters'].get(cid, {}).get('assets', {}).get(kind, {})
            if destination.exists() and previous.get('url') == url and sha256(destination.read_bytes()).hexdigest() == previous.get('sha256'):
                entry[kind] = f'/images/characters/{destination.name}'
                entry['assets'][kind] = previous
                continue
            try:
                raw = fetch(url)
                if expected and sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != expected['sha']:
                    raise ValueError('Git blob checksum mismatch')
                with Image.open(BytesIO(raw)) as original:
                    original.load()
                    if original.format != 'PNG' or min(original.size) < 100:
                        raise ValueError('Invalid or undersized PNG')
                    image = original.convert('RGBA')
                    source_size = image.size
                    if kind == 'avatar':
                        image.thumbnail((96, 96), Image.Resampling.LANCZOS)
                    # Full original canvas, lossless WebP, preserved alpha.
                    image.save(destination, 'WEBP', lossless=True, method=4, exact=True)
                    info = {'source': source, 'url': url, 'matching': match, 'original_sha256': sha256(raw).hexdigest(),
                            'sha256': sha256(destination.read_bytes()).hexdigest(), 'original_bytes': len(raw),
                            'bytes': destination.stat().st_size, 'source_size': source_size, 'size': image.size,
                            'alpha': True, 'lossless': True}
                entry[kind] = f'/images/characters/{destination.name}'
                entry['assets'][kind] = info
            except (OSError, ValueError) as exc:
                entry['errors'].append(f'{kind}: {exc}')
        entry['status'] = 'full' if entry['splash'] else ('avatar_only' if entry['avatar'] else 'missing')
        print(cid, row['slug'], entry['status'], flush=True)
        return cid, entry

    characters = dict(ThreadPoolExecutor(max_workers=4).map(process, rows))
    counts = {key: sum(r['status'] == key for r in characters.values()) for key in ['full', 'avatar_only', 'missing', 'not_processed']}
    manifest = {'version': 1, 'checked_on': '2026-10-29', 'pilot': args.pilot, 'counts': counts, 'characters': characters}
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(counts), flush=True)


if __name__ == '__main__':
    main()
