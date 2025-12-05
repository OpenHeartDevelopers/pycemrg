# src/pycemrg/files/output.py

from pathlib import Path
from typing import Union

class OutputManager:
    """
    Manages output paths with a consistent directory and prefix.
    
    This class's responsibility is to generate full, absolute Path objects
    for output files based on a given directory, a prefix, and a dynamic suffix.
    It does not hold any knowledge of specific pipeline filenames.
    """
    def __init__(self, output_dir: Union[str, Path], output_prefix: str):
        """
        Initializes the manager and ensures the output directory exists.

        Args:
            output_dir (Union[str, Path]): The directory where all files will be saved.
            output_prefix (str): The prefix for all generated filenames.
        """
        self.output_dir = Path(output_dir).resolve()
        self.prefix = output_prefix
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, suffix: str) -> Path:
        """
        Constructs the full, absolute path for a file with a given suffix.

        Args:
            suffix (str): The descriptive suffix for the file, including the
                          extension (e.g., '_segmentation.nii.gz').

        Returns:
            pathlib.Path: The absolute path for the output file.
        """
        if not suffix or not isinstance(suffix, str):
            raise ValueError("Suffix must be a non-empty string.")
            
        filename = f"{self.prefix}{suffix}"
        return self.output_dir / filename