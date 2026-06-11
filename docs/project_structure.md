# Структура репозитория

Обновлено: 11.06.2026

## Текущая структура

```
.
├── apps/
│   ├── portfolio/
│   │   ├── content/                    # JSON-контент сайта (Data Layer)
│   │   │   ├── basic_content.json
│   │   │   ├── main.json
│   │   │   ├── constructor.json
│   │   │   ├── planner.json
│   │   │   ├── developer.json
│   │   │   ├── technologist.json
│   │   │   ├── portfolio_projects.json
│   │   │   ├── work_places.json
│   │   │   ├── education.json
│   │   │   ├── values.json
│   │   │   ├── polzovatelskoe_soglashenie.json
│   │   │   ├── politika_konfidencialnosti.json
│   │   │   └── robots.txt
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── scripts/
│   │   │   └── run_dev.py
│   │   ├── src/
│   │   │   └── portfolio/
│   │   │       ├── __init__.py
│   │   │       ├── config.py
│   │   │       ├── dependencies.py   # загрузка контента, шаблонов, settings
│   │   │       ├── i18n.py           # строки feedback API
│   │   │       ├── feedback_db.py
│   │   │       ├── main.py           # FastAPI app, static mount, middleware
│   │   │       ├── presentation.py   # загрузка layout JSON (@lru_cache)
│   │   │       ├── layout/           # раскладка и параметры анимации
│   │   │       │   └── developer_portfolio_bubbles.json
│   │   │       ├── routers/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── pages.py      # маршруты HTML-страниц (тонкий слой)
│   │   │       │   └── feedback.py   # API формы обратной связи
│   │   │       ├── services/         # Application Layer: подготовка view-model
│   │   │       │   ├── content.py    # локализация и слияние JSON
│   │   │       │   ├── profession.py # профессии, плитки технологий
│   │   │       │   ├── portfolio.py  # ассеты портфолио, пузырьки
│   │   │       │   ├── page_context.py # сборка контекста шаблонов
│   │   │       │   └── html_sanitize.py # санация HTML перед |safe
│   │   │       ├── static/
│   │   │       │   ├── assets/
│   │   │       │   │   ├── icons/
│   │   │       │   │   ├── img/
│   │   │       │   │   └── projects/ # <id>. <название>/PNG|PDF|…
│   │   │       │   ├── css/
│   │   │       │   │   ├── base.css
│   │   │       │   │   ├── portfolio-layout.css
│   │   │       │   │   ├── components/
│   │   │       │   │   └── pages/
│   │   │       │   └── js/
│   │   │       └── templates/
│   │   │           ├── base.html
│   │   │           ├── main.html
│   │   │           ├── profession.html
│   │   │           ├── constructor.html
│   │   │           ├── planner.html
│   │   │           ├── developer.html
│   │   │           ├── technologist.html
│   │   │           └── partials/
│   │   └── tests/
│   │       ├── test_pages.py
│   │       └── test_html_sanitize.py
│   └── sandbox/
├── docs/
│   ├── project_structure.md
│   ├── prompt_requirements.md
│   └── roadmap.md
├── temp/
└── README.md
```

## Слои приложения

| Слой         | Расположение                 | Ответственность                          |
|--------------|------------------------------|------------------------------------------|
| Data         | `content/`                   | Тексты, i18n, метаданные проектов        |
| Presentation | `layout/`, `presentation.py` | Координаты, анимация (без текстов)       |
| Application  | `services/`, `routers/`      | Маршрутизация, view-model, санация, i18n |
| Template     | `templates/`                 | Разметка без бизнес-логики               |
| Style        | `static/css/`                | Визуальное оформление                    |
| Animation    | `layout/` + `static/js/`     | Параметры в JSON, физика в JS            |

## Планируемые расширения

- `apps/platform` — будущий фронтенд или API-шлюз верхнего уровня.
- `apps/sandbox` — независимые демонстрационные проекты.
- `services/<name>` (корень репозитория) — микросервисы с собственным FastAPI.
- `db/`, `infra/` — БД, CI/CD, деплой.
