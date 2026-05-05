# src/pycemrg/files/project.py

import logging
import re
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class InvalidProjectNameError(ValueError):
    """Raised when a requested project name fails validation."""


def _validate_project_name(name: str) -> None:
    if not _NAME_PATTERN.match(name):
        raise InvalidProjectNameError(
            f"Invalid project name '{name}'. "
            "Allowed characters: lowercase letters, digits, and hyphens. "
            "Must start with a letter or digit."
        )


def _python_package_name(project_name: str) -> str:
    """Convert a hyphenated project name to a valid Python package identifier."""
    return project_name.replace("-", "_")


_GITIGNORE = """\
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
env/
.cache/
outputs/
.DS_Store
"""


def _pyproject(project_name: str, with_src: bool) -> str:
    pkg = _python_package_name(project_name)
    packages_block = (
        '\n[tool.setuptools.packages.find]\nwhere = ["src"]\n' if with_src else ""
    )
    return f"""\
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Cardiac imaging project built on the pycemrg suite."
requires-python = ">=3.9"
dependencies = [
    "pycemrg",
    "pycemrg-image-analysis",
    "pycemrg-meshing",
    "pycemrg-model-creation",
]
{packages_block}"""


def _readme(project_name: str, with_src: bool) -> str:
    pkg = _python_package_name(project_name)
    src_section = (
        f"\n## Layout\n\n"
        f"- `scripts/` — runnable orchestrators (file I/O, env injection, path construction).\n"
        f"- `src/{pkg}/` — stateless logic imported from your scripts.\n"
        f"- `config/` — YAML manifests. Generate starter files with `pycemrg init-labels` and `pycemrg init-models`.\n"
        f"- `outputs/` — generated artifacts (gitignored).\n"
        if with_src
        else f"\n## Layout\n\n"
        f"- `scripts/` — runnable orchestrators. Start here.\n"
        f"- `config/` — YAML manifests. Generate starter files with `pycemrg init-labels` and `pycemrg init-models`.\n"
        f"- `outputs/` — generated artifacts (gitignored).\n"
        f"\nWhen `scripts/` outgrows itself, add a `src/{pkg}/` package for reusable logic.\n"
    )
    return f"""\
# {project_name}

A cardiac imaging project built on the pycemrg suite.

## Install

### 1. (Once per machine) Get the `pycemrg` CLI

The CLI is what you used to scaffold this project. Install it with `pipx`
so it stays isolated from your system Python and is available on PATH
regardless of which environment you have activated:

```bash
pipx install pycemrg
```

### 2. Create a project environment

Conda is the recommended choice for cardiac-imaging stacks (handles non-Python
deps cleanly):

```bash
conda create -n {project_name} python=3.11
conda activate {project_name}
```

If you prefer plain venv:

```bash
python -m venv .venv && source .venv/bin/activate
```

### 3. Install this project and the suite

The suite libraries are typically developed alongside your project. Install
them from local checkouts so your edits are picked up immediately:

```bash
pip install -e ../pycemrg
pip install -e ../pycemrg-image-analysis
pip install -e ../pycemrg-meshing
pip install -e ../pycemrg-model-creation
pip install -e .
```
{src_section}
## Run the example

```bash
python scripts/example_run.py
```
"""


_EXAMPLE_RUN = '''\
"""Canonical orchestrator for a pycemrg-suite project.

Demonstrates the suite's wiring pattern:
  - setup_logging configures the root logger once, here in the orchestrator.
  - LabelManager translates anatomical names <-> integer labels.
  - OutputManager owns the output directory and filename prefix.
  - CommandRunner executes external tools safely.

Library code under src/ should accept these objects as dependencies and
remain stateless. The orchestrator is the only place that touches the
filesystem, environment, or process boundary.
"""

import logging
from pathlib import Path

from pycemrg.core.logs import setup_logging
from pycemrg.data import LabelManager
from pycemrg.files import OutputManager
from pycemrg.system import CommandRunner

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def main() -> None:
    setup_logging(log_level=logging.INFO, log_file=OUTPUT_DIR / "run.log")
    log = logging.getLogger(__name__)

    # Generate config/labels.yaml first with: pycemrg init-labels -o config/labels.yaml
    labels = LabelManager(CONFIG_DIR / "labels.yaml")
    log.info("Loaded %d label definitions", len(labels._labels))

    outputs = OutputManager(output_dir=OUTPUT_DIR, output_prefix="case01")
    runner = CommandRunner(logger=log)

    # Replace this block with your real pipeline. The pattern is:
    #   1. Resolve names/groups -> integer tags via labels.
    #   2. Compose output paths via outputs.get_path("_suffix.ext").
    #   3. Hand cmd + expected_outputs to runner.run().
    log.info("Example wiring complete. Output dir: %s", outputs.output_dir)


if __name__ == "__main__":
    main()
'''


class ProjectScaffolder:
    """Creates a starter directory layout for projects that consume the pycemrg suite."""

    def create_project(
        self,
        name: str,
        parent_dir: Union[str, Path] = ".",
        with_src: bool = False,
        force: bool = False,
    ) -> Path:
        """
        Create a new project skeleton at ``parent_dir / name``.

        Args:
            name: Project name. Must match ``[a-z0-9][a-z0-9-]*``.
            parent_dir: Directory in which the project folder will be created.
            with_src: If True, also create ``src/<name>/`` with a stub module
                and add a setuptools packages block to ``pyproject.toml``.
            force: If True, allow writing into an existing non-empty project
                directory (existing files will be overwritten file-by-file).

        Returns:
            Absolute path to the created project root.
        """
        _validate_project_name(name)

        project_root = (Path(parent_dir) / name).resolve()
        if project_root.exists() and any(project_root.iterdir()) and not force:
            raise FileExistsError(
                f"Project directory '{project_root}' already exists and is not empty. "
                "Use force=True to write into it anyway."
            )

        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "scripts").mkdir(exist_ok=True)
        (project_root / "config").mkdir(exist_ok=True)
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        (outputs_dir / ".gitkeep").write_text("")

        (project_root / ".gitignore").write_text(_GITIGNORE)
        (project_root / "pyproject.toml").write_text(_pyproject(name, with_src))
        (project_root / "README.md").write_text(_readme(name, with_src))
        (project_root / "scripts" / "example_run.py").write_text(_EXAMPLE_RUN)

        if with_src:
            pkg = _python_package_name(name)
            src_pkg = project_root / "src" / pkg
            src_pkg.mkdir(parents=True, exist_ok=True)
            (src_pkg / "__init__.py").write_text(
                f'"""Library code for {name}. Imported by orchestrators in scripts/."""\n'
            )
            (src_pkg / "core.py").write_text(
                '"""Stateless logic lives here. Orchestrators in scripts/ inject dependencies."""\n\n'
                "def hello() -> str:\n"
                f'    return "hello from {pkg}"\n'
            )

        logger.info("Created project skeleton at %s", project_root)
        return project_root
