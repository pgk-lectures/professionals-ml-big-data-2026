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
    # Рельеф меняется заметно медленнее, чем GPS-координаты.
    # Кэшируем примерно по сетке ~100 м, чтобы не перегружать внешний API.
    key = f"elev_{lat:.3f}_{lon:.3f}"

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

    # Погодные сетки грубее GPS-точек, поэтому соседние точки маршрута
    # безопасно используют один закэшированный погодный ответ.
    key = f"weather_{lat:.2f}_{lon:.2f}_{date}"

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


def route_osm_objects(track_id: str, points):
    """
    Один запрос Overpass на весь маршрут, затем локально отбираем
    объекты в радиусе 500 м для каждой точки.
    """
    key = f"osm_route_{track_id}"

    def producer():
        lats = [p["latitude"] for p in points]
        lons = [p["longitude"] for p in points]

        # Запас больше 500 м, чтобы не потерять объекты возле крайних точек.
        south = min(lats) - 0.01
        north = max(lats) + 0.01
        west = min(lons) - 0.015
        east = max(lons) + 0.015

        bbox = f"{south},{west},{north},{east}"
        query = f"""
[out:json][timeout:25];
(
  nwr({bbox})["natural"];
  nwr({bbox})["landuse"];
  nwr({bbox})["highway"];
  nwr({bbox})["waterway"];
  nwr({bbox})["place"];
  nwr({bbox})["amenity"="drinking_water"];
);
out tags center;
"""
        url = "https://overpass-api.de/api/interpreter?" + urlencode({"data": query})
        return get_json(url)

    try:
        return cache_json(key, producer).get("elements", [])
    except Exception as exc:
        print(f"[WARN] overpass {track_id}: {exc}")
        return []


def element_position(element):
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if center and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None


def haversine_m(lat1, lon1, lat2, lon2):
    radius = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def objects_within_500m(elements, lat, lon):
    result = []
    for element in elements:
        position = element_position(element)
        if not position:
            continue
        obj_lat, obj_lon = position
        if haversine_m(lat, lon, obj_lat, obj_lon) <= 500:
            result.append(element)
    return result


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
    processed_tracks = 0

    for item in load_manifest():
        path = TRACKS_DIR / f"{item['id']}.gpx"
        if not path.exists():
            continue

        points = parse_gpx(path)
        osm_for_route = route_osm_objects(item["id"], points)
        processed_tracks += 1

        for point in points:
            lat = point["latitude"]
            lon = point["longitude"]
            nearby = objects_within_500m(osm_for_route, lat, lon)
            terrain, objects = classify(nearby)

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

    if not rows:
        raise RuntimeError("Нет загруженных GPX. Сначала запустите 01_download_tracks.py")

    df = pd.DataFrame(rows)
    target = WORK_DIR / "dataset.csv"
    df.to_csv(target, index=False)
    print(f"[OK] обработано маршрутов: {processed_tracks}")
    print(f"[OK] {target}: {len(df)} строк")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
