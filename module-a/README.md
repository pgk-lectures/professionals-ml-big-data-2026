# Практика по модулю А

Основная пошаговая статья: [docs/module-a.md](../docs/module-a.md)

Быстрый старт:

~~~bash
cd module-a
conda env create -f environment.yml
conda activate professionals-ml

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=professionals
export DB_USER=postgres
export DB_PASSWORD=postgres

bash run.sh
~~~

Скрипты специально разбиты по критериям, чтобы при ошибке можно было перезапустить только нужный этап.
