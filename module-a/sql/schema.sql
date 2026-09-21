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
    elevation DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    terrain_type TEXT,
    nearby_objects TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (track_id, point_index)
);
