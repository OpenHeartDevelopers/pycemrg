# src/pycemrg/files/scaffold.py

import logging
from pathlib import Path
from typing import Union

# Use importlib.resources for robust access to package data
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Fallback for Python < 3.9
    import importlib_resources as pkg_resources

from . import templates

logger = logging.getLogger(__name__)


class ConfigScaffolder:
    """
    Handles the creation of template configuration files for pycemrg.
    
    This provides a programmatic API for scaffolding, which can be used
    by a CLI, a GUI, or any other part of an application.
    """

    def _get_template_content(self, template_name: str) -> str:
        """Reads content from a template file within the package."""
        try:
            return pkg_resources.files(templates).joinpath(template_name).read_text()
        except FileNotFoundError:
            logger.error(f"Internal template '{template_name}' not found.")
            raise

    def _write_file(self, output_path: Path, content: str, overwrite: bool):
        """Writes content to a file, checking for existence."""
        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists at '{output_path}'. Use overwrite=True to replace it."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        logger.info(f"Successfully created template file at: {output_path.resolve()}")

    def create_models_manifest(
        self,
        output_path: Union[str, Path] = "models.yaml",
        overwrite: bool = False,
    ):
        """
        Creates a starter models.yaml file.

        Args:
            output_path (Union[str, Path]): Path to save the new file.
            overwrite (bool): If True, will overwrite an existing file.
        """
        content = self._get_template_content("models.yaml.template")
        self._write_file(Path(output_path), content, overwrite)

    def create_labels_manifest(
        self,
        output_path: Union[str, Path] = "labels.yaml",
        overwrite: bool = False,
    ):
        """
        Creates a starter labels.yaml file.

        Args:
            output_path (Union[str, Path]): Path to save the new file.
            overwrite (bool): If True, will overwrite an existing file.
        """
        content = self._get_template_content("labels.yaml.template")
        self._write_file(Path(output_path), content, overwrite)