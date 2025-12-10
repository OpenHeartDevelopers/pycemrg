# src/pycemrg/models/manager.py

import yaml
import hashlib
import logging
import zipfile
import urllib.request
from pathlib import Path
from tqdm import tqdm
from typing import Union

# A library should GET a logger, not configure it. The application does the configuration.
logger = logging.getLogger(__name__)

class TqdmUpTo(tqdm):
    """Provides `update_to(block_num, block_size, total_size)` for urllib."""
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

class ModelManager:
    """
    Manages downloading, caching, and providing paths to versioned ML models.
    Reads a manifest file to determine model URLs, hashes, and final file paths.
    """
    def __init__(self, manifest_path: Union[str, Path], cache_dir: Union[str, Path, None] = None):
        """
        Initializes the ModelManager.

        Args:
            manifest_path (Union[str, Path]): Path to the models YAML manifest.
            cache_dir (Union[str, Path, None], optional): Directory to store
                downloads. Defaults to '~/.cache/pycemrg'.
        """
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Model manifest not found at {self.manifest_path}")
        
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

    def get_model_path(self, model_name: str, version: str = 'default') -> Path:
        """
        Gets the local path to a model file, handling downloads and unzipping.
        """
        if model_name not in self._manifest:
            raise KeyError(f"Model '{model_name}' not found in manifest.")
        
        model_info = self._manifest[model_name]
        version_key = version if version != 'default' else model_info['default']
        
        if version_key not in model_info['versions']:
            raise KeyError(f"Version '{version_key}' for model '{model_name}' not found.")
            
        version_info = model_info['versions'][version_key]
        url = version_info['url']
        
        if url.startswith("file://"):
            project_root = self.manifest_path.parent
            local_path = project_root / url[7:]
            if not local_path.exists():
                raise FileNotFoundError(f"Local model file not found: {local_path}")
            return local_path.resolve()

        filename = Path(url).name
        cached_zip_path = self.cache_dir / filename
        unzip_dir = self.cache_dir / filename.replace('.zip', '')

        # DECOUPLED LOGIC: The path inside the zip is now read from the manifest
        unzipped_target_filename = version_info.get('unzipped_target_path')
        if not unzipped_target_filename:
            raise ValueError(f"'unzipped_target_path' not specified in manifest for {model_name}:{version_key}")
        
        final_model_path = unzip_dir / unzipped_target_filename

        if final_model_path.exists():
            logger.info(f"Found prepared model in cache: {final_model_path}")
            return final_model_path

        if cached_zip_path.exists():
            logger.info(f"Found model archive '{filename}' in cache. Verifying...")
            try:
                if self._verify_hash(cached_zip_path, version_info.get('sha256')):
                    logger.info("Integrity check passed. Unzipping...")
                    with zipfile.ZipFile(cached_zip_path, 'r') as zip_ref:
                        zip_ref.extractall(unzip_dir)
                    return final_model_path
            except IOError as e:
                logger.warning(f"{e}. Re-downloading...")
                cached_zip_path.unlink()

        logger.info(f"Downloading '{filename}' from {url}...")
        try:
            with TqdmUpTo(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc=filename) as t:
                urllib.request.urlretrieve(url, filename=cached_zip_path, reporthook=t.update_to)
            
            self._verify_hash(cached_zip_path, version_info.get('sha256'))
            logger.info("Download complete. Unzipping...")
            with zipfile.ZipFile(cached_zip_path, 'r') as zip_ref:
                zip_ref.extractall(unzip_dir)
            return final_model_path
        except Exception as e:
            if cached_zip_path.exists():
                cached_zip_path.unlink() # Clean up failed download
            raise RuntimeError(f"Failed to process model '{filename}'. Error: {e}") from e