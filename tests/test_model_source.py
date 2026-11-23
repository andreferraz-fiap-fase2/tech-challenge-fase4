from pathlib import Path

import pytest

from voc.infrastructure.model_source import (
    clear_if_outdated,
    ensure_installed,
    expected_source,
    record_source,
)

SETTINGS = {"generation_model": "Qwen/Qwen3-1.7B", "generation_revision": "abc123"}


def test_weights_from_another_model_are_refused_before_loading(tmp_path: Path) -> None:
    folder = tmp_path / "generation"
    record_source(folder, {"repo_id": "Qwen/Qwen3-0.6B", "revision": "old"})
    with pytest.raises(RuntimeError, match="Qwen3-0.6B@old.*app.py models"):
        ensure_installed(folder, expected_source(SETTINGS, "generation"))


def test_folder_without_marker_is_refused(tmp_path: Path) -> None:
    folder = tmp_path / "generation"
    folder.mkdir()
    with pytest.raises(RuntimeError, match="sem marcador"):
        ensure_installed(folder, expected_source(SETTINGS, "generation"))


def test_outdated_weights_are_cleared_and_matching_ones_kept(tmp_path: Path) -> None:
    folder = tmp_path / "generation"
    expected = expected_source(SETTINGS, "generation")
    record_source(folder, {"repo_id": "Qwen/Qwen3-0.6B", "revision": "old"})
    (folder / "model.safetensors").write_bytes(b"old")
    clear_if_outdated(folder, expected)
    assert not folder.exists()
    record_source(folder, expected)
    (folder / "model-00001-of-00002.safetensors").write_bytes(b"new")
    clear_if_outdated(folder, expected)
    ensure_installed(folder, expected)
    assert (folder / "model-00001-of-00002.safetensors").exists()
