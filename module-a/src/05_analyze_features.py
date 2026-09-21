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
    df["season"] = df["month"].map(lambda x: season(int(x)) if pd.notna(x) else "unknown")
    df["elevation_band"] = pd.cut(
        df["elevation"],
        bins=[-np.inf, 100, 200, 400, np.inf],
        labels=["low", "medium", "high", "very_high"],
    )

    enriched = WORK_DIR / "dataset_enriched.csv"
    df.to_csv(enriched, index=False)

    numeric_cols = ["cadence", "elevation", "temperature"]
    corr = df[numeric_cols].corr(numeric_only=True)

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
| track_id | идентификатор маршрута | — | связь точек одного трека |
| date | дата маршрута | дата | сезонность |
| region | регион | — | географическая группировка |
| latitude | широта | градусы | координата |
| longitude | долгота | градусы | координата |
| cadence | частота шагов | шаг/мин | активность туриста |
| elevation | высота над уровнем моря | м | характеристика рельефа |
| temperature | температура воздуха | °C | погодные условия |
| terrain_type | тип местности | категория | характеристика окружения |
| nearby_objects | объекты в радиусе 500 м | список | контекст точки |
| month | месяц | 1–12 | всесезонность |
| season | сезон | категория | всесезонность |
| elevation_band | высотная категория | категория | упрощённая характеристика рельефа |
"""
    (WORK_DIR / "data_dictionary.md").write_text(dictionary, encoding="utf-8")

    conclusions = ["# Проверка распределений", ""]

    for column in numeric_cols:
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
