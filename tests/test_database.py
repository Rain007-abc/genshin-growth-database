import sys
import gc
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from init_db import build_database  # noqa: E402
from planner import get_connection, calculate_plan, set_inventory, list_characters  # noqa: E402


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.temp.name) / "new.db"
        cls.result = build_database(cls.db)

    @classmethod
    def tearDownClass(cls):
        # sqlite3's context manager commits but does not close connections.
        # Collect released connections before Windows removes the temporary DB.
        gc.collect()
        cls.temp.cleanup()

    def test_complete_data_and_foreign_keys(self):
        self.assertEqual(self.result["characters"],120)
        self.assertEqual(self.result["materials"],309)
        with get_connection(self.db) as conn:
            self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0],1)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(),[])
            self.assertEqual(len(list_characters(conn)),120)

    def test_xiangling_full_ascension_costs(self):
        with get_connection(self.db) as conn:
            cid=conn.execute("SELECT id FROM characters WHERE slug='xiangling'").fetchone()[0]
            plan=calculate_plan(conn,cid,0,6,{"attack":(1,1),"skill":(1,1),"burst":(1,1)})
        by_name={m["name_en"]:m for m in plan["materials"]}
        self.assertEqual(by_name["Jueyun Chili"]["required"],168)
        self.assertEqual(by_name["Everflame Seed"]["required"],46)
        self.assertEqual(by_name["Mora"]["required"],420000)

    def test_talents_are_separate_and_sum(self):
        with get_connection(self.db) as conn:
            cid=conn.execute("SELECT id FROM characters WHERE slug='xiangling'").fetchone()[0]
            plan=calculate_plan(conn,cid,0,0,{"attack":(1,10),"skill":(1,10),"burst":(1,10)})
        by_name={m["name_en"]:m for m in plan["materials"]}
        self.assertEqual(by_name["Crown of Insight"]["required"],3)
        self.assertEqual(by_name["Mora"]["required"],3*1652500)

    def test_inventory_edit_updates_shortage(self):
        with get_connection(self.db) as conn:
            cid=conn.execute("SELECT id FROM characters WHERE slug='xiangling'").fetchone()[0]
            m_id=conn.execute("SELECT id FROM materials WHERE name_en='Jueyun Chili'").fetchone()[0]
            set_inventory(conn,m_id,168)
            plan=calculate_plan(conn,cid,0,6,{"attack":(1,1),"skill":(1,1),"burst":(1,1)})
        chili=next(m for m in plan["materials"] if m["id"]==m_id)
        self.assertEqual(chili["missing"],0)
        self.assertEqual(chili["owned"],168)

    def test_invalid_goals_and_quantities(self):
        with get_connection(self.db) as conn:
            cid=conn.execute("SELECT id FROM characters WHERE slug='xiangling'").fetchone()[0]
            with self.assertRaises(ValueError):
                calculate_plan(conn,cid,4,2)
            with self.assertRaises(ValueError):
                set_inventory(conn,202,-1)
            with self.assertRaises(ValueError):
                set_inventory(conn,202,True)
            with self.assertRaises(Exception):
                conn.execute("INSERT INTO ascension_requirements VALUES (999999999,1,202,1)")

    def test_rebuild_refuses_to_overwrite_inventory(self):
        with self.assertRaises(FileExistsError):
            build_database(self.db)


if __name__=="__main__":
    unittest.main()
