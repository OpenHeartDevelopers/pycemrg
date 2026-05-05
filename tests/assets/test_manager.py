import textwrap
from pathlib import Path

import pytest

from pycemrg.assets import AssetManager


def _write_manifest(tmp_path: Path, body: str) -> Path:
    manifest = tmp_path / "assets.yaml"
    manifest.write_text(textwrap.dedent(body))
    return manifest


def _write_local_asset(tmp_path: Path, relpath: str, content: bytes = b"x") -> Path:
    target = tmp_path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


@pytest.fixture
def local_manifest(tmp_path):
    _write_local_asset(tmp_path, "bin/meshtools3d", b"#!/bin/sh\n")
    return _write_manifest(
        tmp_path,
        """
        meshtools3d:
          default: v1.0
          versions:
            v1.0:
              url: "file://./bin/meshtools3d"
              unzipped_target_path: "meshtools3d"
        """,
    )


def test_missing_manifest_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        AssetManager(tmp_path / "does_not_exist.yaml")


def test_unknown_asset_raises(local_manifest, tmp_path):
    mgr = AssetManager(local_manifest, cache_dir=tmp_path / "cache")
    with pytest.raises(KeyError):
        mgr.get_asset_path("not_a_real_asset")


def test_unknown_version_raises(local_manifest, tmp_path):
    mgr = AssetManager(local_manifest, cache_dir=tmp_path / "cache")
    with pytest.raises(KeyError):
        mgr.get_asset_path("meshtools3d", version="v99.0")


def test_file_url_resolves_relative_to_manifest(local_manifest, tmp_path):
    mgr = AssetManager(local_manifest, cache_dir=tmp_path / "cache")
    resolved = mgr.get_asset_path("meshtools3d")
    assert resolved == (tmp_path / "bin" / "meshtools3d").resolve()
    assert resolved.exists()


def test_file_url_missing_target_raises(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        """
        ghost:
          default: v1.0
          versions:
            v1.0:
              url: "file://./bin/missing"
              unzipped_target_path: "missing"
        """,
    )
    mgr = AssetManager(manifest, cache_dir=tmp_path / "cache")
    with pytest.raises(FileNotFoundError):
        mgr.get_asset_path("ghost")


def test_get_asset_path_and_get_model_path_are_equivalent(local_manifest, tmp_path):
    mgr = AssetManager(local_manifest, cache_dir=tmp_path / "cache")
    assert mgr.get_asset_path("meshtools3d") == mgr.get_model_path("meshtools3d")


def test_default_cache_dir_is_user_cache(local_manifest):
    mgr = AssetManager(local_manifest)
    assert mgr.cache_dir == Path.home() / ".cache" / "pycemrg"
