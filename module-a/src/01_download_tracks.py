import argparse
from urllib.request import Request, urlopen

from common import TRACKS_DIR, load_manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=("all", "provided", "additional"),
        default="all",
        help="Какие треки скачивать",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    if args.source != "all":
        manifest = [item for item in manifest if item["source"] == args.source]

    ok = 0
    for item in manifest:
        target = TRACKS_DIR / f"{item['id']}.gpx"
        request = Request(item["url"], headers={"User-Agent": "pgk-lectures-training/1.0"})
        with urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())
        print(f"[OK] {item['id']} -> {target.name}")
        ok += 1

    print(f"Загружено: {ok}/{len(manifest)} ({args.source})")


if __name__ == "__main__":
    main()
