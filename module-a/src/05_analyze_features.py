from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import DIST_DIR, WORK_DIR


def season(month):
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def jarque_bera(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3 or np.std(x) == 0:
        return 0.0, 1.0, 0.0, 0.0

    z = (x - np.mean(x)) / np.std(x)
    skew = float(np.mean(z ** 3))
    excess = float(np.mean(z ** 4) - 3.0)
    jb = n / 6.0 * (skew ** 2 + (excess ** 2) / 4.0)
    p_value = math.exp(-jb / 2.0)
    return jb, p_value, skew, excess


def main():
    df = pd.read_csv(WORK_DIR / "dataset.csv")
    dt = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    df["month"] = dt.dt.month
    df["hour"] = dt.dt.hour
    df["season"] = df["month"].map(lambda x: season(int(x)) if pd.notna(x) else "unknown")
    df["time_of_day"] = pd.cut(
        df["hour"],
        bins=[-1, 5, 11, 17, 23],
        labels=["night", "morning", "day", "evening"],
    )
    df["elevation_band"] = pd.cut(
        df["elevation"],
        bins=[-np.inf, 100, 200, 400, np.inf],
        labels=["low", "medium", "high", "very_high"],
    )

    enriched = WORK_DIR / "dataset_enriched.csv"
    df.to_csv(enriched, index=False)

    correlation_cols = ["latitude", "longitude", "cadence", "elevation", "temperature", "hour"]
    distribution_cols = ["cadence", "elevation", "temperature"]
    corr = df[correlation_cols].corr(numeric_only=True)

    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(corr.values, vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.index)), corr.index)
    for i in range(len(corr.index)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(WORK_DIR / "correlation.png", dpi=150)
    plt.close(fig)

    dictionary = """# Словарь данных

| Поле | Расшифровка | Единицы | Назначение |
|---|---|---|---|
| track_id | идентификатор конкретного прохождения маршрута | — | связь точек одного трека |
| track_name | название маршрута | — | группировка повторных прохождений одного маршрута |
| source | тип источника: provided/additional | категория | отделяет исходные треки от добавленных |
| date | дата маршрута | дата | сезонность |
| region | регион | — | географическая группировка |
| point_index | порядковый номер точки в треке | номер | уникальность и порядок точек |
| timestamp | дата и время GPS-точки | UTC | анализ времени суток и погоды |
| latitude | широта | градусы | координата |
| longitude | долгота | градусы | координата |
| cadence | частота шагов | шаг/мин | активность туриста |
| elevation | высота над уровнем моря | м | характеристика рельефа |
| temperature | температура воздуха | °C | погодные условия |
| terrain_type | тип местности | категория | характеристика окружения |
| nearby_objects | объекты в радиусе 500 м | список | географический контекст точки |
| month | месяц | 1–12 | сезонная аналитика |
| hour | час суток | 0–23 | анализ температуры и активности по времени суток |
| season | сезон | категория | всесезонность |
| time_of_day | часть суток | категория | фильтрация и аналитика в модуле Б |
| elevation_band | высотная категория | категория | упрощённая характеристика рельефа |
"""
    (WORK_DIR / "data_dictionary.md").write_text(dictionary, encoding="utf-8")

    conclusions = ["# Проверка распределений", ""]

    for column in distribution_cols:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            continue

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(values, bins=min(12, max(4, len(values) // 4)))
        ax.set_title(f"Распределение: {column}")
        ax.set_xlabel(column)
        ax.set_ylabel("Количество")
        fig.tight_layout()
        fig.savefig(DIST_DIR / f"{column}.png", dpi=150)
        plt.close(fig)

        jb, p, skew, excess = jarque_bera(values.to_numpy())
        normal = p >= 0.05
        transform = "не требуется автоматически" if abs(skew) < 0.5 else "стоит рассмотреть преобразование/масштабирование"

        conclusions.extend(
            [
                f"## {column}",
                f"- Jarque–Bera: {jb:.3f}",
                f"- p-value: {p:.4f}",
                f"- skewness: {skew:.3f}",
                f"- excess kurtosis: {excess:.3f}",
                f"- вывод: распределение {'не противоречит нормальному' if normal else 'отличается от нормального'};",
                f"- трансформация: {transform}.",
                "",
            ]
        )

    (WORK_DIR / "conclusions.md").write_text("\n".join(conclusions), encoding="utf-8")
    print(f"[OK] {enriched}")
    print(f"[OK] {WORK_DIR / 'correlation.png'}")
    print(f"[OK] {WORK_DIR / 'data_dictionary.md'}")
    print(f"[OK] {WORK_DIR / 'conclusions.md'}")


if __name__ == "__main__":
    main()
