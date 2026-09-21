CREATE TABLE IF NOT EXISTS tracks (
    track_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    route_date DATE NOT NULL,
    source TEXT NOT NULL,
    gpx_path TEXT,
    map_path TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS route_points (
    track_id TEXT NOT NULL REFERENCES tracks(track_id) ON DELETE CASCADE,
    point_index INTEGER NOT NULL,
    point_time TIMESTAMPTZ,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    cadence DOUBLE PRECISION,
    popularity_score DOUBLE PRECISION,
    elevation DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    terrain_type TEXT,
    nearby_objects TEXT,
    month INTEGER,
    hour INTEGER,
    season TEXT,
    time_of_day TEXT,
    elevation_band TEXT,
    has_water INTEGER,
    has_road INTEGER,
    has_settlement INTEGER,
    has_wetland INTEGER,
    nearby_object_count INTEGER,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (track_id, point_index)
);

-- Позволяет безопасно обновить БД, если таблица была создана старой версией практики.
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS popularity_score DOUBLE PRECISION;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS humidity DOUBLE PRECISION;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS precipitation DOUBLE PRECISION;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS wind_speed DOUBLE PRECISION;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS month INTEGER;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS hour INTEGER;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS season TEXT;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS time_of_day TEXT;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS elevation_band TEXT;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS has_water INTEGER;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS has_road INTEGER;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS has_settlement INTEGER;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS has_wetland INTEGER;
ALTER TABLE route_points ADD COLUMN IF NOT EXISTS nearby_object_count INTEGER;
