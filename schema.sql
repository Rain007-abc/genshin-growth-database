PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name_zh TEXT NOT NULL,
    name_en TEXT NOT NULL,
    element TEXT NOT NULL,
    weapon TEXT NOT NULL,
    region TEXT NOT NULL,
    rarity INTEGER NOT NULL CHECK (rarity BETWEEN 1 AND 5),
    normal_attack TEXT,
    elemental_skill TEXT,
    elemental_burst TEXT
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    name_zh TEXT NOT NULL,
    name_en TEXT NOT NULL,
    category TEXT NOT NULL,
    farm_days TEXT NOT NULL DEFAULT '',
    farm_hint TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ascension_requirements (
    character_id INTEGER NOT NULL REFERENCES characters(id),
    phase INTEGER NOT NULL CHECK (phase BETWEEN 1 AND 6),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (character_id, phase, material_id)
);

CREATE TABLE IF NOT EXISTS talent_requirements (
    character_id INTEGER NOT NULL REFERENCES characters(id),
    to_level INTEGER NOT NULL CHECK (to_level BETWEEN 2 AND 10),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (character_id, to_level, material_id)
);

CREATE TABLE IF NOT EXISTS inventory (
    material_id INTEGER PRIMARY KEY REFERENCES materials(id),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)
);

CREATE TABLE IF NOT EXISTS data_sources (
    source_name TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    revision TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ascension_material ON ascension_requirements(material_id);
CREATE INDEX IF NOT EXISTS idx_talent_material ON talent_requirements(material_id);
CREATE INDEX IF NOT EXISTS idx_material_category ON materials(category);
