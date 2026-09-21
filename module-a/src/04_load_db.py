from __future__ import annotations

import pandas as pd
import psycopg2

from common import MAPS_DIR, MODULE_DIR, TRACKS_DIR, WORK_DIR, db_config, load_manifest


def optional(row, name):
    value = getattr(row, name, None)
    return None if value is None or pd.isna(value) else value


def main():
    enriched_path = WORK_DIR / "dataset_enriched.csv"
    source_path = enriched_path if enriched_path.exists() else WORK_DIR / "dataset.csv"
    df = pd.read_csv(source_path)

    manifest = [
        item
        for item in load_manifest()
        if (TRACKS_DIR / f"{item['id']}.gpx").exists()
    ]

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
                        cadence, elevation, temperature, humidity, precipitation, wind_speed,
                        terrain_type, nearby_objects,
                        month, hour, season, time_of_day, elevation_band,
                        has_water, has_road, has_settlement, has_wetland, nearby_object_count,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        NOW()
                    )
                    ON CONFLICT (track_id, point_index) DO UPDATE SET
                        point_time = EXCLUDED.point_time,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        cadence = EXCLUDED.cadence,
                        elevation = EXCLUDED.elevation,
                        temperature = EXCLUDED.temperature,
                        humidity = EXCLUDED.humidity,
                        precipitation = EXCLUDED.precipitation,
                        wind_speed = EXCLUDED.wind_speed,
                        terrain_type = EXCLUDED.terrain_type,
                        nearby_objects = EXCLUDED.nearby_objects,
                        month = EXCLUDED.month,
                        hour = EXCLUDED.hour,
                        season = EXCLUDED.season,
                        time_of_day = EXCLUDED.time_of_day,
                        elevation_band = EXCLUDED.elevation_band,
                        has_water = EXCLUDED.has_water,
                        has_road = EXCLUDED.has_road,
                        has_settlement = EXCLUDED.has_settlement,
                        has_wetland = EXCLUDED.has_wetland,
                        nearby_object_count = EXCLUDED.nearby_object_count,
                        updated_at = NOW()
                    """,
                    (
                        row.track_id,
                        int(row.point_index),
                        optional(row, "timestamp"),
                        float(row.latitude),
                        float(row.longitude),
                        optional(row, "cadence"),
                        optional(row, "elevation"),
                        optional(row, "temperature"),
                        optional(row, "humidity"),
                        optional(row, "precipitation"),
                        optional(row, "wind_speed"),
                        optional(row, "terrain_type"),
                        optional(row, "nearby_objects") or "",
                        optional(row, "month"),
                        optional(row, "hour"),
                        optional(row, "season"),
                        optional(row, "time_of_day"),
                        optional(row, "elevation_band"),
                        optional(row, "has_water"),
                        optional(row, "has_road"),
                        optional(row, "has_settlement"),
                        optional(row, "has_wetland"),
                        optional(row, "nearby_object_count"),
                    ),
                )

            cur.execute("SELECT COUNT(*) FROM route_points")
            count = cur.fetchone()[0]
            print(f"[OK] источник: {source_path.name}")
            print(f"[OK] route_points: {count} строк")
            print("Повторный запуск должен показать то же количество строк.")


if __name__ == "__main__":
    main()
