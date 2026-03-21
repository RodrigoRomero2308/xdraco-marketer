"""Carga de configuración desde variables de entorno."""

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


def get_env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)
