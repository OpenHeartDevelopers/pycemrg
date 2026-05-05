import textwrap
from pathlib import Path

import pytest

from pycemrg.assets import AssetManager
from pycemrg.models.manager import ModelManager


@pytest.fixture
def local_manifest(tmp_path):
    target = tmp_path / "bin" / "meshtools3d"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"#!/bin/sh\n")

    manifest = tmp_path / "assets.yaml"
    manifest.write_text(textwrap.dedent(
        """
        meshtools3d:
          default: v1.0
          versions:
            v1.0:
              url: "file://./bin/meshtools3d"
              unzipped_target_path: "meshtools3d"
        """
    ))
    return manifest


def test_modelmanager_emits_deprecation_warning(local_manifest, tmp_path):
    with pytest.warns(DeprecationWarning, match="AssetManager"):
        ModelManager(local_manifest, cache_dir=tmp_path / "cache")


def test_modelmanager_behaves_like_assetmanager(local_manifest, tmp_path):
    cache = tmp_path / "cache"
    with pytest.warns(DeprecationWarning):
        legacy = ModelManager(local_manifest, cache_dir=cache)
    new = AssetManager(local_manifest, cache_dir=cache)

    assert legacy.get_model_path("meshtools3d") == new.get_asset_path("meshtools3d")


def test_modelmanager_is_subclass_of_assetmanager():
    assert issubclass(ModelManager, AssetManager)
