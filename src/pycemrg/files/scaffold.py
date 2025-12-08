# src/pycemrg/files/scaffold.py

import logging
import math
from pathlib import Path
from typing import Union

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

from . import templates

logger = logging.getLogger(__name__)


class ConfigScaffolder:
    """Handles the creation of template configuration files for pycemrg."""

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
        """Creates a starter models.yaml file."""
        content = self._get_template_content("models.yaml.template")
        self._write_file(Path(output_path), content, overwrite)

    def create_labels_manifest(
        self,
        output_path: Union[str, Path] = "labels.yaml",
        overwrite: bool = False,
        num_labels: int = 3,
        num_groups: int = 1,
    ):
        """
        Creates a starter labels.yaml file with a specified number of
        placeholder labels and groups.

        Args:
            output_path (Union[str, Path]): Path to save the new file.
            overwrite (bool): If True, will overwrite an existing file.
            num_labels (int): Number of placeholder labels to generate (e.g., structure_1).
            num_groups (int): Number of placeholder groups to generate (e.g., group_a).
        """
        lines = [
            "# pycemrg Label Manifest",
            "# Maps human-readable names to integer values for segmentation masks.",
            "",
            "labels:",
            "  background: 0",
        ]

        if num_labels > 0:
            lines.append("  # --- Auto-generated placeholder labels ---")
            for i in range(1, num_labels + 1):
                lines.append(f"  structure_{i}: {i}")

        if num_groups > 0:
            lines.append("\n" + "groups:")
            lines.append("  # --- Auto-generated placeholder groups ---")
            
            # Distribute labels into groups in chunks
            structure_names = [f"structure_{i}" for i in range(1, num_labels + 1)]
            if num_labels > 0:
                chunk_size = math.ceil(num_labels / num_groups)
            else:
                chunk_size = 0

            for i in range(num_groups):
                group_letter = chr(ord('a') + i)
                lines.append(f"  group_{group_letter}:")
                
                start_index = i * chunk_size
                end_index = start_index + chunk_size
                members = structure_names[start_index:end_index]
                
                if not members:
                    lines.append("    []  # No labels to assign to this group")
                else:
                    for member in members:
                        lines.append(f"    - {member}")

        content = "\n".join(lines)
        self._write_file(Path(output_path), content, overwrite)