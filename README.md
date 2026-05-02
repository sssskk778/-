# Carrier Rating Platform v2

Что реализовано:
- загрузка CSV-датасета с предрассчитанными критериями C1..C16;
- выбор критериев для сценария оценки;
- объективный расчет весов энтропийным методом;
- TOPSIS с автоматически рассчитанными весами;
- роли admin / user;
- просмотр результатов и экспорт CSV;
- диагностический расчет в интерфейсе через диаграммы, а не JSON;
- Dockerfile и docker-compose.

## Быстрый старт
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python bootstrap.py
python run.py
```

## Docker
```bash
docker compose up --build
docker-compose up -d
```

## CSV-формат
Обязательная колонка: `company_name`.
Дополнительно можно передавать `country`, `service_type`.
Критерии: `C1 ... C16`.

В комплекте есть файл:
`data/sample_real_carriers_dataset.csv`

## Учётные записи
- admin / admin123
- user / user123
