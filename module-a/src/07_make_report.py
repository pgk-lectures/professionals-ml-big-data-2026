from __future__ import annotations

import pandas as pd

from common import AUG_DIR, MAPS_DIR, WORK_DIR, load_manifest


def main():
    dataset = pd.read_csv(WORK_DIR / "dataset_enriched.csv")
    manifest = load_manifest()

    map_files = sorted(p.name for p in MAPS_DIR.glob("*.png"))
    aug_files = sorted(p.name for p in AUG_DIR.glob("*.png"))

    sample = dataset.head(8).to_markdown(index=False)

    text = f"""# Отчёт по модулю А

## 1. Цель

Собрать и предварительно обработать данные туристических маршрутов для последующих модулей анализа и машинного обучения.

## 2. Результат

- маршрутов в манифесте: {len(manifest)};
- точек в датасете: {len(dataset)};
- карт с маршрутами: {len(map_files)};
- аугментированных изображений: {len(aug_files)};
- итоговый набор: work/dataset_enriched.csv;
- база данных: PostgreSQL, таблицы tracks и route_points.

## 3. Источники

Учебная реализация использует:
- OpenTopoMap — топографический фон и легенда;
- Open-Meteo — температура и высота;
- OpenStreetMap / Overpass API — объекты в радиусе 500 м.

Выбор этих сервисов является учебной реализацией; конкурсное задание требует внешние источники, но не фиксирует конкретного провайдера.

## 4. Структура БД

- tracks — метаданные маршрутов;
- route_points — точки, погода, рельеф, местность и объекты;
- первичный ключ точек: track_id + point_index;
- повторная загрузка выполняется через UPSERT и не создаёт дубли.

## 5. Пример данных

{sample}

## 6. Карты

{chr(10).join(f"- work/maps/{name}" for name in map_files)}

## 7. Предобработка

Добавлены признаки month, season и elevation_band.
Корреляционная матрица сохранена в work/correlation.png.
Описание полей: work/data_dictionary.md.
Проверка распределений: work/conclusions.md и work/distributions/.

## 8. Аугментация

Использованы простые преобразования: поворот, сдвиг и изменение яркости.
Координаты исходных точек в БД при этом не меняются.

## 9. Форматы результатов

- GPX — исходные треки;
- PNG — карты и аугментации;
- CSV — набор данных;
- PostgreSQL — структурированное хранение;
- Markdown — словарь данных, выводы и отчёт.
"""

    target = WORK_DIR / "report.md"
    target.write_text(text, encoding="utf-8")
    print(f"[OK] {target}")


if __name__ == "__main__":
    main()
