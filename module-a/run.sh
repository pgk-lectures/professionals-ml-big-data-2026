#!/usr/bin/env bash
set -euo pipefail

python src/01_download_tracks.py
python src/02_build_dataset.py
python src/03_make_maps.py
python src/04_load_db.py
python src/05_analyze_features.py
python src/06_augment_images.py
python src/07_make_report.py

echo
echo "Модуль А завершён. Результаты: module-a/work/"
