# Практика по модулю А

Основная пошаговая статья: [docs/module-a.md](../docs/module-a.md)

## Быстрый запуск для домашней проверки

~~~bash
cd module-a

conda env create -f environment.yml
conda activate professionals-ml

docker compose -f compose.yml up -d

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=professionals
export DB_USER=postgres
export DB_PASSWORD=postgres

bash run.sh
~~~

`run.sh` прогоняет все **20 учебных маршрутов** через полный pipeline.

Для обучения лучше сначала пройти [пошаговую статью](../docs/module-a.md) вручную: она объясняет, зачем нужен каждый этап и какой критерий он закрывает.

Скрипты специально разбиты по этапам, чтобы при ошибке можно было перезапустить только нужную часть.
