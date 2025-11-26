"""Утилиты для получения версии приложения."""

from functools import lru_cache
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10
    import tomli as tomllib  # type: ignore[no-redef]


@lru_cache
def get_version() -> str:
    """Возвращает версию приложения из pyproject.toml."""

    project_root = Path(__file__).resolve().parents[4]
    pyproject_path = project_root / "apps" / "portfolio" / "pyproject.toml"

    with pyproject_path.open("rb") as pyproject_file:
        pyproject_data = tomllib.load(pyproject_file)

    return pyproject_data["tool"]["poetry"]["version"]

