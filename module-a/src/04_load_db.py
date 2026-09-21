from __future__ import annotations

import pandas as pd
import psycopg2

from common import MAPS_DIR, MODULE_DIR, TRACKS_DIR, WORK_DIR, db_config, load_manifest


def main():
    df = pd.read_csv(WORK_DIR / "dataset.csv")
    manifest = load_manifest()

    with psycopg2.connect(**db_config()) as conn:
        with conn.cursor() as cur:
            cur.execute((MODULE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8"))

            for item in manifest:
                cur.execute(
                    """
                    INSERT INTO tracks
                        (track_id, name, region, route_date, source, gpx_path, map_path, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (track_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        region = EXCLUDED.region,
                        route_date = EXCLUDED.route_date,
                        source = EXCLUDED.source,
                        gpx_path = EXCLUDED.gpx_path,
                        map_path = EXCLUDED.map_path,
                        updated_at = NOW()
                    """,
                    (
                        item["id"],
                        item["name"],
                        item["region"],
                        item["date"],
                        item["source"],
                        str(TRACKS_DIR / f"{item['id']}.gpx"),
                        str(MAPS_DIR / f"{item['id']}.png"),
                    ),
                )

            for row in df.itertuples(index=False):
                cur.execute(
                    """
                    INSERT INTO route_points (
                        track_id, point_index, point_time, latitude, longitude,
                        cadence, elevation, temperature, terrain_type, nearby_objects, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (track_id, point_index) DO UPDATE SET
                        point_time = EXCLUDED.point_time,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        cadence = EXCLUDED.cadence,
                        elevation = EXCLUDED.elevation,
                        temperature = EXCLUDED.temperature,
                        terrain_type = EXCLUDED.terrain_type,
                        nearby_objects = EXCLUDED.nearby_objects,
                        updated_at = NOW()
                    """,
                    (
                        row.track_id,
                        int(row.point_index),
                        row.timestamp if pd.notna(row.timestamp) else None,
                        float(row.latitude),
                        float(row.longitude),
                        float(row.cadence) if pd.notna(row.cadence) else None,
                        float(row.elevation) if pd.notna(row.elevation) else None,
                        float(row.temperature) if pd.notna(row.temperature) else None,
                        row.terrain_type,
                        row.nearby_objects if pd.notna(row.nearby_objects) else "",
                    ),
                )

            cur.execute("SELECT COUNT(*) FROM route_points")
            count = cur.fetchone()[0]
            print(f"[OK] route_points: {count} строк")
            print("Повторный запуск должен показать то же количество строк.")


if __name__ == "__main__":
    main()
