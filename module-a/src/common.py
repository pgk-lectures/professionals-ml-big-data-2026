from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = MODULE_DIR.parent
WORK_DIR = MODULE_DIR / "work"
TRACKS_DIR = WORK_DIR / "tracks"
MAPS_DIR = WORK_DIR / "maps"
AUG_DIR = WORK_DIR / "augmented"
DIST_DIR = WORK_DIR / "distributions"
CACHE_DIR = WORK_DIR / "cache"
MANIFEST_PATH = REPO_DIR / "training-data" / "tracks.json"

for directory in (WORK_DIR, TRACKS_DIR, MAPS_DIR, AUG_DIR, DIST_DIR, CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def parse_gpx(path: Path):
    root = ET.parse(path).getroot()
    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    points = []
    for index, node in enumerate(root.findall(".//g:trkpt", ns)):
        lat = float(node.attrib["lat"])
        lon = float(node.attrib["lon"])
        ele_node = node.find("g:ele", ns)
        time_node = node.find("g:time", ns)

        cadence = None
        for child in node.iter():
            if child.tag.split("}")[-1].lower() == "cadence" and child.text:
                cadence = float(child.text)
                break

        points.append(
            {
                "point_index": index,
                "latitude": lat,
                "longitude": lon,
                "gpx_elevation": float(ele_node.text) if ele_node is not None else None,
                "timestamp": time_node.text if time_node is not None else None,
                "cadence": cadence,
            }
        )
    return points


def cache_json(name: str, producer):
    path = CACHE_DIR / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    value = producer()
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return value


def db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "professionals"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }
