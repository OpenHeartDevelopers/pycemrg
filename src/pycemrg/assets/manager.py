# src/pycemrg/assets/manager.py

import yaml
import hashlib
import logging
import tarfile
import zipfile
import urllib.request
from pathlib import Path
from tqdm import tqdm
from typing import Union

logger = logging.getLogger(__name__)

# Archive suffixes recognised by the AssetManager, longest-first so that
# multi-part suffixes (e.g. '.tar.gz') are matched before their tails ('.gz').
_ARCHIVE_SUFFIXES = (
    '.tar.gz', '.tar.bz2', '.tar.xz',
    '.tgz', '.tbz2', '.txz',
    '.zip', '.tar',
)


class TqdmUpTo(tqdm):
    """Provides `update_to(block_num, block_size, total_size)` for urllib."""
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


class AssetManager:
    """
    Manages downloading, caching, and providing paths to versioned assets.

    Reads a manifest file to determine asset URLs, hashes, and final file
    paths. The asset can be anything fetched + verified + cached: ML model
    weights, compiled binaries, reference datasets, atlases, etc.
    """
    def __init__(self, manifest_path: Union[str, Path], cache_dir: Union[str, Path, None] = None):
        """
        Initializes the AssetManager.

        Args:
            manifest_path (Union[str, Path]): Path to the assets YAML manifest.
            cache_dir (Union[str, Path, None], optional): Directory to store
                downloads. Defaults to '~/.cache/pycemrg'.
        """
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Asset manifest not found at {self.manifest_path}")

        if cache_dir is None:
            self.cache_dir = Path.home() / '.cache' / 'pycemrg'
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._manifest = self._load_manifest()

    def _load_manifest(self):
        with open(self.manifest_path, 'r') as f:
            return yaml.safe_load(f)

    def _verify_hash(self, file_path: Path, expected_hash: str) -> bool:
        """Verifies the SHA256 hash of a file."""
        if not expected_hash:
            logger.debug(f"No hash provided for {file_path.name}. Skipping verification.")
            return True

        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        actual_hash = hasher.hexdigest()
        if actual_hash != expected_hash:
            raise IOError(
                f"File hash mismatch for {file_path.name}.\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}"
            )
        return True

    @staticmethod
    def _archive_stem(filename: str) -> str:
        """Strips a known archive suffix to derive the extraction directory name.

        Falls back to :pyattr:`Path.stem` for unrecognised extensions so the
        caller still gets a sensible directory name.
        """
        lower = filename.lower()
        for suffix in _ARCHIVE_SUFFIXES:
            if lower.endswith(suffix):
                return filename[: -len(suffix)]
        return Path(filename).stem

    @staticmethod
    def _is_within_directory(directory: Path, target: Path) -> bool:
        """Returns True if ``target`` resolves to a path inside ``directory``."""
        directory = directory.resolve()
        target = target.resolve()
        return directory == target or directory in target.parents

    def _extract_archive(self, archive_path: Path, dest_dir: Path) -> None:
        """Extracts a zip or tar archive into ``dest_dir``.

        Tar members are validated so that no entry escapes ``dest_dir`` via an
        absolute path or ``..`` traversal before anything is written.

        Args:
            archive_path (Path): The archive to extract.
            dest_dir (Path): Target directory; created if it does not exist.

        Raises:
            ValueError: If the archive type is unsupported or a tar member
                would extract outside ``dest_dir``.
        """
        name = archive_path.name.lower()
        dest_dir = Path(dest_dir)

        if name.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
            return

        if any(name.endswith(s) for s in ('.tar', '.tar.gz', '.tgz',
                                          '.tar.bz2', '.tbz2', '.tar.xz', '.txz')):
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                for member in tar_ref.getmembers():
                    member_path = dest_dir / member.name
                    if not self._is_within_directory(dest_dir, member_path):
                        raise ValueError(
                            f"Refusing to extract '{member.name}': path escapes "
                            f"the extraction directory ({dest_dir})."
                        )
                tar_ref.extractall(dest_dir)
            return

        raise ValueError(
            f"Unsupported archive type for '{archive_path.name}'. "
            f"Supported: {', '.join(_ARCHIVE_SUFFIXES)}."
        )

    def get_model_path(self, model_name: str, version: str = 'default') -> Path:
        """
        Gets the local path to an asset file, handling downloads and unzipping.

        The parameter is named ``model_name`` for backwards compatibility with
        the original ``ModelManager`` API. New code should prefer
        :meth:`get_asset_path`.
        """
        if model_name not in self._manifest:
            raise KeyError(f"Asset '{model_name}' not found in manifest.")

        model_info = self._manifest[model_name]
        version_key = version if version != 'default' else model_info['default']

        if version_key not in model_info['versions']:
            raise KeyError(f"Version '{version_key}' for asset '{model_name}' not found.")

        version_info = model_info['versions'][version_key]
        url = version_info['url']

        if url.startswith("file://"):
            project_root = self.manifest_path.parent
            local_path = project_root / url[7:]
            if not local_path.exists():
                raise FileNotFoundError(f"Local asset file not found: {local_path}")
            return local_path.resolve()

        filename = Path(url).name
        cached_archive_path = self.cache_dir / filename
        extract_dir = self.cache_dir / self._archive_stem(filename)

        unzipped_target_filename = version_info.get('unzipped_target_path')
        if not unzipped_target_filename:
            raise ValueError(f"'unzipped_target_path' not specified in manifest for {model_name}:{version_key}")

        final_model_path = extract_dir / unzipped_target_filename

        if final_model_path.exists():
            logger.info(f"Found prepared asset in cache: {final_model_path}")
            return final_model_path

        if cached_archive_path.exists():
            logger.info(f"Found asset archive '{filename}' in cache. Verifying...")
            try:
                if self._verify_hash(cached_archive_path, version_info.get('sha256')):
                    logger.info("Integrity check passed. Extracting...")
                    self._extract_archive(cached_archive_path, extract_dir)
                    return final_model_path
            except IOError as e:
                logger.warning(f"{e}. Re-downloading...")
                cached_archive_path.unlink()

        logger.info(f"Downloading '{filename}' from {url}...")
        try:
            with TqdmUpTo(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc=filename) as t:
                urllib.request.urlretrieve(url, filename=cached_archive_path, reporthook=t.update_to)

            self._verify_hash(cached_archive_path, version_info.get('sha256'))
            logger.info("Download complete. Extracting...")
            self._extract_archive(cached_archive_path, extract_dir)
            return final_model_path
        except Exception as e:
            if cached_archive_path.exists():
                cached_archive_path.unlink()
            raise RuntimeError(f"Failed to process asset '{filename}'. Error: {e}") from e

    def get_asset_path(self, asset_name: str, version: str = 'default') -> Path:
        """Canonical name for asset retrieval; delegates to :meth:`get_model_path`."""
        return self.get_model_path(model_name=asset_name, version=version)
