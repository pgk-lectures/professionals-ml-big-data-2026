from __future__ import annotations

import json
import math
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from common import TRACKS_DIR, WORK_DIR, cache_json, load_manifest, parse_gpx


def get_json(url: str):
    request = Request(url, headers={"User-Agent": "pgk-lectures-training/1.0"})
    with urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def elevation(lat: float, lon: float, fallback):
    key = f"elev_{lat:.5f}_{lon:.5f}"

    def producer():
        query = urlencode({"latitude": lat, "longitude": lon})
        data = get_json(f"https://api.open-meteo.com/v1/elevation?{query}")
        value = data.get("elevation")
        if isinstance(value, list):
            value = value[0] if value else None
        return {"value": value}

    try:
        value = cache_json(key, producer).get("value")
        return float(value) if value is not None else fallback
    except Exception as exc:
        print(f"[WARN] elevation {lat},{lon}: {exc}")
        return fallback


def temperature(lat: float, lon: float, timestamp: str | None):
    if not timestamp:
        return None
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    date = dt.date().isoformat()
    key = f"weather_{lat:.4f}_{lon:.4f}_{date}"

    def producer():
        query = urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "start_date": date,
                "end_date": date,
                "hourly": "temperature_2m",
                "timezone": "UTC",
            }
        )
        return get_json(f"https://archive-api.open-meteo.com/v1/archive?{query}")

    try:
        data = cache_json(key, producer)
        times = data.get("hourly", {}).get("time", [])
        values = data.get("hourly", {}).get("temperature_2m", [])
        wanted = dt.strftime("%Y-%m-%dT%H:00")
        if wanted in times:
            return values[times.index(wanted)]
        return values[0] if values else None
    except Exception as exc:
        print(f"[WARN] weather {lat},{lon}: {exc}")
        return None


def overpass_objects(lat: float, lon: float):
    key = f"osm_{lat:.4f}_{lon:.4f}"

    def producer():
        query = f"""
[out:json][timeout:25];
(
  nwr(around:500,{lat},{lon})["natural"];
  nwr(around:500,{lat},{lon})["landuse"];
  nwr(around:500,{lat},{lon})["highway"];
  nwr(around:500,{lat},{lon})["waterway"];
  nwr(around:500,{lat},{lon})["place"];
  nwr(around:500,{lat},{lon})["amenity"="drinking_water"];
);
out tags center 50;
"""
        url = "https://overpass-api.de/api/interpreter?" + urlencode({"data": query})
        return get_json(url)

    try:
        return cache_json(key, producer).get("elements", [])
    except Exception as exc:
        print(f"[WARN] overpass {lat},{lon}: {exc}")
        return []


def classify(elements):
    types = []
    labels = []

    for element in elements:
        tags = element.get("tags", {})

        if tags.get("natural") == "wetland":
            types.append("wetland")
        if tags.get("natural") in {"wood", "tree_row"} or tags.get("landuse") == "forest":
            types.append("forest")
        if "waterway" in tags or tags.get("natural") == "water":
            types.append("water")
        if "highway" in tags:
            types.append("road")
        if "place" in tags or "building" in tags:
            types.append("settlement")

        for key in ("natural", "landuse", "highway", "waterway", "place", "amenity"):
            if key in tags:
                labels.append(f"{key}={tags[key]}")

    priority = ["wetland", "forest", "water", "road", "settlement"]
    terrain = next((x for x in priority if x in types), "other")
    return terrain, ";".join(sorted(set(labels))[:20])


def main():
    rows = []

    for item in load_manifest():
        path = TRACKS_DIR / f"{item['id']}.gpx"
        if not path.exists():
            raise FileNotFoundError(f"Нет {path}. Сначала запустите 01_download_tracks.py")

        for point in parse_gpx(path):
            lat = point["latitude"]
            lon = point["longitude"]
            osm = overpass_objects(lat, lon)
            terrain, objects = classify(osm)

            rows.append(
                {
                    "track_id": item["id"],
                    "track_name": item["name"],
                    "source": item["source"],
                    "date": item["date"],
                    "region": item["region"],
                    "point_index": point["point_index"],
                    "timestamp": point["timestamp"],
                    "latitude": lat,
                    "longitude": lon,
                    "cadence": point["cadence"],
                    "elevation": elevation(lat, lon, point["gpx_elevation"]),
                    "temperature": temperature(lat, lon, point["timestamp"]),
                    "terrain_type": terrain,
                    "nearby_objects": objects,
                }
            )

    df = pd.DataFrame(rows)
    target = WORK_DIR / "dataset.csv"
    df.to_csv(target, index=False)
    print(f"[OK] {target}: {len(df)} строк")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
