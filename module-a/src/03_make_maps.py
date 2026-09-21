from __future__ import annotations

import math
from io import BytesIO
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
import numpy as np

from common import MAPS_DIR, TRACKS_DIR, WORK_DIR, load_manifest, parse_gpx


TILE_SIZE = 256
ZOOM = 12


def tile_xy(lat, lon, zoom=ZOOM):
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def download_tile(x, y, z=ZOOM):
    url = f"https://a.tile.opentopomap.org/{z}/{x}/{y}.png"
    req = Request(url, headers={"User-Agent": "pgk-lectures-training/1.0"})
    with urlopen(req, timeout=30) as response:
        return plt.imread(BytesIO(response.read()), format="png")


def make_map(track_id, points):
    xy = [tile_xy(p["latitude"], p["longitude"]) for p in points]
    xs = [p[0] for p in xy]
    ys = [p[1] for p in xy]

    min_x = math.floor(min(xs)) - 1
    max_x = math.floor(max(xs)) + 1
    min_y = math.floor(min(ys)) - 1
    max_y = math.floor(max(ys)) + 1

    width = (max_x - min_x + 1) * TILE_SIZE
    height = (max_y - min_y + 1) * TILE_SIZE
    canvas = np.ones((height, width, 4), dtype=float)

    for ty in range(min_y, max_y + 1):
        for tx in range(min_x, max_x + 1):
            try:
                tile = download_tile(tx, ty)
                y0 = (ty - min_y) * TILE_SIZE
                x0 = (tx - min_x) * TILE_SIZE
                canvas[y0:y0 + TILE_SIZE, x0:x0 + TILE_SIZE, : tile.shape[2]] = tile
            except Exception as exc:
                print(f"[WARN] tile {tx}/{ty}: {exc}")

    px = [(x - min_x) * TILE_SIZE for x in xs]
    py = [(y - min_y) * TILE_SIZE for y in ys]

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(canvas)
    ax.plot(px, py, linewidth=3)
    ax.scatter([px[0], px[-1]], [py[0], py[-1]], s=45)
    ax.set_title(track_id)
    ax.axis("off")
    target = MAPS_DIR / f"{track_id}.png"
    fig.savefig(target, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {target}")


def main():
    created = 0
    for item in load_manifest():
        path = TRACKS_DIR / f"{item['id']}.gpx"
        if not path.exists():
            continue
        make_map(item["id"], parse_gpx(path))
        created += 1

    if created == 0:
        raise RuntimeError("Нет загруженных GPX. Сначала запустите 01_download_tracks.py")

    legend = """# Легенда топографической карты

Источник: официальная легенда OpenTopoMap — https://opentopomap.org/about

| Категория в датасете | Что ищем на карте/в легенде |
|---|---|
| forest | лесные площади: лиственный, хвойный, смешанный лес; зелёные лесные обозначения |
| wetland | болота, торфяники, камышовые/заболоченные территории |
| water | реки, озёра и другие водные объекты; синие обозначения |
| road | дороги, тропы и дорожные линии из раздела «Straßen und Wege» |
| settlement | населённые пункты и застроенные территории |
| other | участок, который не удалось уверенно отнести к категориям выше |

В учебном решении OSM/Overpass используется для автоматического поиска объектов,
а легенда OpenTopoMap — для интерпретации и проверки того, как эти объекты
отображаются на топографической карте.

На соревновании в отчёте нужно показать несколько конкретных примеров:
фрагмент карты → обозначение/цвет по легенде → получившийся terrain_type.
"""
    (WORK_DIR / "map_legend.md").write_text(legend, encoding="utf-8")
    print(f"[OK] {WORK_DIR / 'map_legend.md'}")


if __name__ == "__main__":
    main()
