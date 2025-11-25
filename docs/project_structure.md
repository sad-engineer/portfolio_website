# Структура репозитория

Обновлено: 25.11.2025

## Текущая структура

```
.
├── apps/
│   ├── portfolio/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── scripts/
│   │   │   └── run_dev.py
│   │   ├── src/
│   │   │   └── portfolio/
│   │   │       ├── __init__.py
│   │   │       ├── config.py
│   │   │       ├── dependencies.py
│   │   │       ├── main.py
│   │   │       ├── routers/
│   │   │       │   ├── __init__.py
│   │   │       │   └── pages.py
│   │   │       ├── services/
│   │   │       │   └── __init__.py
│   │   │       ├── static/
│   │   │       │   ├── assets/
│   │   │       │   │   └── img/
│   │   │       │   ├── css/
│   │   │       │   └── js/
│   │   │       └── templates/
│   │   │           ├── index.html
│   │   │           └── sections/
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_pages.py
│   └── sandbox/
├── docs/
│   └── project_structure.md
├── temp/
│   ├── startbootstrap-resume-gh-pages/
│   └── tic_tac_toe/
└── README.md
```

## Планируемые расширения

- `apps/platform` — будущий фронтенд или API-шлюз верхнего уровня.
- `apps/sandbox` — независимые демонстрационные проекты (например, игры).
- `services/<name>` — микросервисы, каждый с собственным FastAPI-приложением.
- `db/` — конфигурации баз данных, миграции, docker-compose.
- `infra/` — Dockerfile, CI/CD, Kubernetes-манифесты.
- `scripts/` и `Makefile` — общие скрипты и команды для разработки.

