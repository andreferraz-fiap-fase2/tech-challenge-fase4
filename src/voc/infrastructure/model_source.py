"""Marcador da origem dos pesos locais, conferido antes de carregar um modelo.

A pasta models/<tipo> não guarda a revisão baixada. Ao trocar o gerador em
config/models.json, pesos antigos seriam carregados em silêncio; o marcador impede isso.
"""

import shutil
from pathlib import Path

from voc.infrastructure.storage import read_json, write_json

MARKER = "source.json"


def expected_source(settings: dict[str, object], kind: str) -> dict[str, str]:
    """Origem exigida pela configuração, ex.: expected_source(cfg, "generation")."""
    return {
        "repo_id": str(settings[f"{kind}_model"]),
        "revision": str(settings[f"{kind}_revision"]),
    }


def installed_source(folder: Path) -> dict[str, object] | None:
    marker = folder / MARKER
    return read_json(marker) if marker.exists() else None


def clear_if_outdated(folder: Path, expected: dict[str, str]) -> None:
    """Remove pesos de outra origem para não misturar arquivos de dois modelos."""
    if folder.exists() and installed_source(folder) != expected:
        shutil.rmtree(folder)


def record_source(folder: Path, expected: dict[str, str]) -> None:
    write_json(folder / MARKER, expected)


def ensure_installed(folder: Path, expected: dict[str, str]) -> None:
    installed = installed_source(folder)
    if installed == expected:
        return
    found = f"{installed['repo_id']}@{installed['revision']}" if installed else "sem marcador"
    raise RuntimeError(
        f"Os pesos em {folder} ({found}) não correspondem a config/models.json "
        f"({expected['repo_id']}@{expected['revision']}). "
        "Execute: uv run python app.py models"
    )
