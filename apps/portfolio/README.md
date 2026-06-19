# Portfolio App

Персональный сайт-визитка на FastAPI и Jinja2. Содержит шаблон, статические ассеты и базовую структуру приложения для дальнейшего расширения.

## Деплой на Render

В репозитории добавлен `render.yaml`, поэтому проще всего деплоить через Blueprint.

1. Запушить изменения в GitHub-репозиторий.
2. В Render выбрать `New` -> `Blueprint`.
3. Подключить репозиторий и подтвердить создание сервиса `portfolio`.
4. Дождаться первого билда и открыть URL сервиса.

Render возьмёт команды из `render.yaml`:

- `buildCommand`: клон git submodules PET-проектов из `apps/*`, затем установка Poetry и зависимостей только `apps/portfolio`
- `startCommand`: запуск `uvicorn` на порту из переменной окружения `PORT`

### PET-проекты (submodules)

Веб-демо PET-проектов (например, `apps/tic_tac_toe`) встраиваются в тот же процесс FastAPI — отдельные Web Service на Render для них не нужны.

При деплое достаточно:

1. Подтянуть submodule (`git submodule update --init --recursive` — уже в `buildCommand`)
2. Установить зависимости портфолио — их хватает для веб-API и шаблонов PET-проектов
3. Не устанавливать ML/десктоп-зависимости PET-проектов (torch, numpy и т.п.) — они не используются при встраивании

Локально клон с submodules:

```bash
git clone --recurse-submodules <url>
# или после обычного clone:
git submodule update --init --recursive
```

Для этого приложения отдельные переменные окружения не обязательны, но при необходимости их можно добавить в панели Render (`Environment`).

