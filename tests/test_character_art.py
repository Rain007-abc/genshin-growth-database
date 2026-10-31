"""Image routes and existing API regressions, using an isolated copy of SQLite."""
from contextlib import closing
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app
from planner import get_connection


class CharacterArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.temp.name) / 'api-test.db'
        with closing(sqlite3.connect((ROOT / 'genshin_growth.db').as_uri() + '?mode=ro', uri=True)) as original:
            with closing(sqlite3.connect(cls.db)) as copied:
                original.backup(copied)
        cls.connection_patch = patch.object(app, 'get_connection', lambda: closing(get_connection(cls.db)))
        cls.connection_patch.start()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.connection_patch.stop()
        cls.temp.cleanup()

    def request(self, path, data=None):
        request = Request(self.base + path, data=None if data is None else json.dumps(data).encode(),
                          headers={'Content-Type': 'application/json'})
        return urlopen(request, timeout=10)

    def json(self, path, data=None):
        with self.request(path, data) as response:
            return json.load(response)

    def test_manifest_covers_exact_database_ids(self):
        characters = self.json('/api/characters')
        manifest = self.json('/images/characters/manifest.json')
        self.assertEqual({str(c['id']) for c in characters}, set(manifest['characters']))
        self.assertEqual(len(characters), 120)
        self.assertFalse(manifest['pilot'])
        self.assertEqual(manifest['counts']['not_processed'], 0)
        for c in characters:
            art = manifest['characters'][str(c['id'])]
            for key in ['id', 'slug', 'name_en', 'name_zh']:
                self.assertEqual(c[key], art[key])

    def test_every_listed_image_is_served_with_correct_type(self):
        manifest = self.json('/images/characters/manifest.json')
        for row in manifest['characters'].values():
            for kind in ['avatar', 'splash']:
                if not row[kind]:
                    continue
                with self.subTest(id=row['id'], kind=kind), self.request(row[kind]) as response:
                    self.assertEqual(response.headers['Content-Type'], 'image/webp')
                    self.assertEqual(response.read(4), b'RIFF')
                    self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')

    def test_placeholder_and_missing_image(self):
        with self.request('/images/characters/placeholder.svg') as response:
            self.assertEqual(response.headers['Content-Type'], 'image/svg+xml')
        with self.assertRaises(HTTPError) as error:
            self.request('/images/characters/99999999.webp')
        self.assertEqual(error.exception.code, 404)
        self.assertTrue(self.json('/api/health')['ok'])

    def test_paths_cannot_escape_image_directory(self):
        for path in ['/images/characters/../../genshin_growth.db', '/images/characters/%2e%2e/app.py',
                     '/images/characters/..%5c..%5capp.py', '/images/characters/10000023.webp/../app.py',
                     '/images/characters/characters.json', '/images/characters/10000023.png',
                     '/images/characters/C:%5cWindows%5cwin.ini']:
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)

    def test_plan_and_inventory_api_on_test_copy(self):
        path = '/api/plan?character_id=10000023&from_phase=0&to_phase=6&attack_to=1&skill_to=1&burst_to=1'
        plan = self.json(path)
        chili = next(m for m in plan['materials'] if m['name_en'] == 'Jueyun Chili')
        self.assertEqual(chili['required'], 168)
        self.assertTrue(self.json('/api/inventory', {'material_id': chili['id'], 'quantity': 168})['ok'])
        updated = next(m for m in self.json(path)['materials'] if m['id'] == chili['id'])
        self.assertEqual((updated['owned'], updated['missing']), (168, 0))
        stats = self.json('/api/stats')
        self.assertEqual((stats['characters'], stats['materials']), (120, 309))


if __name__ == '__main__':
    unittest.main()
