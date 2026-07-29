# pycemrg Core Library - API Reference

## Overview

The pycemrg library provides a decoupled, configuration-driven system for managing common development and research tasks, including Machine Learning models, anatomical labels, file management, and system command execution. The core principle is that the library is stateless and generic; the consuming application provides configuration to direct its behavior.

**Typical Workflow:**

1. (Optional) Use the `ConfigScaffolder` or the `pycemrg` CLI to generate template configuration files.
2. Populate these YAML files with application-specific data.
3. Instantiate the required managers (`ModelManager`, `LabelManager`, `OutputManager`, `CommandRunner`).
4. Use the manager instances to retrieve model paths, translate label values, generate output paths, and execute external processes.

---

## 1. Configuration Scaffolding

**Entry Point:** `pycemrg.files.ConfigScaffolder`

Programmatically creates template configuration files. This is the recommended first step for a new project.

**Instantiation:**
```python
from pycemrg.files import ConfigScaffolder
scaffolder = ConfigScaffolder()
```

**Methods:**

### `.create_models_manifest()`
Creates a starter `models.yaml` file with usage examples.

*   **Signature:** `(output_path: Union[str, Path] = "models.yaml", overwrite: bool = False) -> None`
*   **Args:**
    *   `output_path` (str | Path): The location to save the new file. Defaults to `"models.yaml"`.
    *   `overwrite` (bool): If `True`, will overwrite an existing file at the `output_path`. Defaults to `False`.
*   **Raises:**
    *   `FileExistsError`: If the file at `output_path` exists and `overwrite` is `False`.

**Example:**
```python
scaffolder = ConfigScaffolder()
scaffolder.create_models_manifest(output_path="config/models.yaml", overwrite=True)
```

---

### `.create_labels_manifest()`
Creates a starter `labels.yaml` file with customizable placeholder structure.

*   **Signature:** `(output_path: Union[str, Path] = "labels.yaml", overwrite: bool = False, num_labels: int = 3, num_groups: int = 1) -> None`
*   **Args:**
    *   `output_path` (str | Path): The location to save the new file. Defaults to `"labels.yaml"`.
    *   `overwrite` (bool): If `True`, will overwrite an existing file at the `output_path`. Defaults to `False`.
    *   `num_labels` (int): Number of placeholder labels to generate (e.g., `structure_1`, `structure_2`). Defaults to 3.
    *   `num_groups` (int): Number of placeholder groups to generate (e.g., `group_a`, `group_b`). Labels are distributed evenly across groups. Defaults to 1.
*   **Raises:**
    *   `FileExistsError`: If the file at `output_path` exists and `overwrite` is `False`.

**Example:**
```python
scaffolder = ConfigScaffolder()
scaffolder.create_labels_manifest(
    output_path="config/labels.yaml",
    num_labels=10,
    num_groups=3,
    overwrite=True
)
```

**Generated Structure:**
```yaml
labels:
  background: 0
  structure_1: 1
  structure_2: 2
  # ...

groups:
  group_a:
    - structure_1
    - structure_2
  group_b:
    - structure_3
    # ...
```

---

## 2. File Path Management

**Entry Point:** `pycemrg.files.OutputManager`

Generates consistent output paths with a centralized prefix/suffix pattern. This utility is critical for orchestrators managing multiple related output files while maintaining naming conventions.

**Instantiation:**
```python
from pycemrg.files import OutputManager
from pathlib import Path

# Initialize with output directory and file prefix
mgr = OutputManager(
    output_dir="/path/to/output",
    output_prefix="case_01"
)
```

**Methods:**

### `.get_path()`
Constructs the full, absolute path for a file with a given suffix.

*   **Signature:** `(suffix: str) -> Path`
*   **Args:**
    *   `suffix` (str): The descriptive suffix for the file, including the extension (e.g., `"_segmentation.nii.gz"`, `"_mesh.vtk"`).
*   **Returns:**
    *   `pathlib.Path`: The absolute path for the output file.
*   **Raises:**
    *   `ValueError`: If `suffix` is empty or not a string.

**Behavior:**
- Creates the output directory if it doesn't exist (on initialization)
- Returns paths as `{output_dir}/{prefix}{suffix}`

**Example:**
```python
mgr = OutputManager("/data/results", "patient_042")

seg_path = mgr.get_path("_segmentation.nii.gz")
# Returns: /data/results/patient_042_segmentation.nii.gz

mesh_path = mgr.get_path("_heart_mesh.vtk")
# Returns: /data/results/patient_042_heart_mesh.vtk
```

**Design Rationale:**
`OutputManager` enforces consistency without imposing rigid structure. It's the orchestrator's responsibility to define meaningful suffixes; the manager ensures they're applied uniformly.

---

## 3. Model Management

**Entry Point:** `pycemrg.models.ModelManager`

Manages downloading, caching, and providing local filesystem paths to ML models defined in a manifest. Models are versioned, integrity-verified via SHA256, and cached to avoid redundant downloads.

**Instantiation:**
```python
from pycemrg.models import ModelManager
from pathlib import Path

# The path to your application's models.yaml is required.
model_manager = ModelManager(manifest_path=Path("path/to/your/models.yaml"))

# Optionally, specify a custom cache directory.
model_manager = ModelManager(
    manifest_path=Path("path/to/your/models.yaml"),
    cache_dir=Path("/tmp/my-app-cache")  # Default: ~/.cache/pycemrg
)
```

**Manifest Format:**
```yaml
segmentation_model:
  default: v2.1
  versions:
    v2.1:
      url: "https://example.com/models/seg_v2.1.zip"
      sha256: "abc123def456..."
      unzipped_target_path: "checkpoints/model.pth"
    v2.0:
      url: "file://local/path/to/seg_v2.0.zip"
      sha256: "xyz789..."
      unzipped_target_path: "model.pth"
```

**Methods:**

### `.get_model_path()`
The primary method. Returns the local path to a model's weights, handling download, verification, and unzipping as needed. **The operation is idempotent**; subsequent calls for the same model return the cached path instantly without network activity.

*   **Signature:** `(model_name: str, version: str = 'default') -> Path`
*   **Args:**
    *   `model_name` (str): The logical name of the model (a top-level key in `models.yaml`).
    *   `version` (str): The specific version to retrieve. If `'default'`, uses the version specified by the `default` key in the manifest.
*   **Returns:**
    *   `pathlib.Path`: A resolved, absolute path to the ready-to-use model file.
*   **Raises:**
    *   `FileNotFoundError`: If the provided `manifest_path` does not exist, or if a `file://` URL points to a missing local file.
    *   `KeyError`: If the `model_name` or `version` is not found in the manifest.
    *   `ValueError`: If the manifest entry is malformed (e.g., missing `unzipped_target_path`).
    *   `IOError`: If the downloaded file's SHA256 hash does not match the manifest.
    *   `RuntimeError`: If a network, extraction, or file system error occurs during processing.

**Example:**
```python
manager = ModelManager("models.yaml")

# Get default version
model_path = manager.get_model_path("segmentation_model")
# First call: Downloads, verifies, extracts → /home/user/.cache/pycemrg/.../model.pth
# Subsequent calls: Returns cached path immediately

# Get specific version
legacy_path = manager.get_model_path("segmentation_model", version="v2.0")
```

**Design Rationale:**
- Models are never auto-updated to prevent silent breaking changes in production environments.
- Hash verification is mandatory (unless omitted in manifest) to detect corruption or man-in-the-middle attacks.
- Local `file://` URLs support air-gapped or institutional network scenarios.

---

## 4. Label Management

**Entry Point:** `pycemrg.data.LabelManager`

Manages translations between human-readable label names, groups, and their corresponding integer values based on a label manifest. Supports hierarchical group definitions for complex anatomical structures.

**Instantiation:**
```python
from pycemrg.data import LabelManager
from pathlib import Path

# The path to your application's labels.yaml is required.
label_manager = LabelManager(config_path=Path("path/to/your/labels.yaml"))
```

**Manifest Format:**
```yaml
labels:
  background: 0
  LV_myo: 2
  RV_myo: 3
  LA_wall: 4
  RA_wall: 5

groups:
  ventricles:
    - LV_myo
    - RV_myo
  atria:
    - LA_wall
    - RA_wall
  all_chambers:
    - ventricles  # Groups can reference other groups
    - atria
```

**Methods:**

### `.get_value()`
Translates a single label name to its integer value.

*   **Signature:** `(name: str) -> int`
*   **Args:**
    *   `name` (str): The human-readable label name (e.g., `"LV_myo"`).
*   **Returns:**
    *   `int`: The corresponding integer value.
*   **Raises:**
    *   `KeyError`: If `name` is not defined in the manifest's `labels` section.

**Example:**
```python
lv_value = label_manager.get_value("LV_myo")  # Returns: 2
```

---

### `.get_name()`
Translates an integer value back to its human-readable name.

*   **Signature:** `(value: int) -> str`
*   **Args:**
    *   `value` (int): The integer value of the label.
*   **Returns:**
    *   `str`: The corresponding human-readable name.
*   **Raises:**
    *   `KeyError`: If `value` is not defined in the manifest's `labels` section.

**Example:**
```python
name = label_manager.get_name(2)  # Returns: "LV_myo"
```

---

### `.get_values_from_names()`
Translates a list of strings into a sorted, unique list of integer label values. The input list can contain individual label names, group names (recursively resolved), or numbers as strings.

*   **Signature:** `(names: List[str]) -> List[int]`
*   **Args:**
    *   `names` (List[str]): A list of strings to translate. Can include keys from `labels`, keys from `groups`, or numeric strings (e.g., `['ventricles', 'LA_wall', '5']`).
*   **Returns:**
    *   `List[int]`: A sorted list of unique integer values corresponding to the input names.
*   **Raises:**
    *   `KeyError`: If any name in the list is not a valid label, group, or parseable integer. The error message includes all available keys.

**Example:**
```python
# Mix of individual labels, groups, and raw integers
values = label_manager.get_values_from_names(["ventricles", "LA_wall", "0"])
# Returns: [0, 2, 3, 4] (sorted, deduplicated)

# Recursive group resolution
all_values = label_manager.get_values_from_names(["all_chambers"])
# Returns: [2, 3, 4, 5]
```

---

### `.get_tags_string()`
Convenience method that returns a comma-separated string of tag values. Useful for command-line tools that expect tag lists as strings.

*   **Signature:** `(names: List[str], separator: str = ",") -> str`
*   **Args:**
    *   `names` (List[str]): A list of label/group names to resolve.
    *   `separator` (str): The character to use between values. Defaults to `","`.
*   **Returns:**
    *   `str`: A separator-delimited string of integer values.

**Example:**
```python
tags = label_manager.get_tags_string(["ventricles", "atria"])
# Returns: "2,3,4,5"

# Custom separator for tool compatibility
tags = label_manager.get_tags_string(["LV_myo", "RV_myo"], separator=":")
# Returns: "2:3"
```

**Design Rationale:**
- `LabelManager` never validates that integer values make sense (e.g., non-negative, unique). It's a pure translation layer.
- Groups support recursive definitions to model anatomical hierarchies.
- Numeric strings are accepted to support mixed-mode orchestrators that may receive raw tag values.

---

## 5. Label Mapping Between Standards

**Entry Point:** `pycemrg.data.LabelMapper`

Maps between two different label standards (e.g., source segmentation labels → simulation mesh tags). Uses composition of two `LabelManager` instances to create bidirectional translations based on shared anatomical names.

**Instantiation:**
```python
from pycemrg.data import LabelManager, LabelMapper
from pathlib import Path

# Define two different label standards
source_mgr = LabelManager("source_labels.yaml")  # e.g., clinical segmentation
target_mgr = LabelManager("target_labels.yaml")  # e.g., simulation mesh

# Create mapper
mapper = LabelMapper(source=source_mgr, target=target_mgr)
```

**Example Manifests:**

**source_labels.yaml:**
```yaml
labels:
  LV_myo: 100
  RV_myo: 101
  LA_wall: 102
```

**target_labels.yaml:**
```yaml
labels:
  LV_myo: 2
  RV_myo: 3
  LA_wall: 4
```

**Methods:**

### `.get_source_to_target_mapping()`
Generates a dictionary mapping source integer tags to target integer tags. Only labels with matching names are included.

*   **Signature:** `() -> Dict[int, int]`
*   **Returns:**
    *   `Dict[int, int]`: A dictionary of `{source_tag: target_tag}`.

**Example:**
```python
mapper = LabelMapper(source_mgr, target_mgr)
mapping = mapper.get_source_to_target_mapping()
# Returns: {100: 2, 101: 3, 102: 4}

# Use in mesh relabeling
for source_val, target_val in mapping.items():
    mesh_array[mesh_array == source_val] = target_val
```

---

### `.get_source_tags()`
Convenience method to resolve names/groups using the source standard.

*   **Signature:** `(names: List[str]) -> List[int]`
*   **Returns:**
    *   `List[int]`: Resolved tags from the source `LabelManager`.

**Equivalent to:** `mapper.source.get_values_from_names(names)`

---

### `.get_target_tags()`
Convenience method to resolve names/groups using the target standard.

*   **Signature:** `(names: List[str]) -> List[int]`
*   **Returns:**
    *   `List[int]`: Resolved tags from the target `LabelManager`.

**Equivalent to:** `mapper.target.get_values_from_names(names)`

**Example:**
```python
# Extract source mesh with clinical labels
source_tags = mapper.get_source_tags(["LV_myo", "RV_myo"])  # [100, 101]

# Validate target mesh has simulation labels
target_tags = mapper.get_target_tags(["LV_myo", "RV_myo"])  # [2, 3]
```

**Design Rationale:**
- `LabelMapper` never modifies the underlying `LabelManager` instances; it's purely a query interface.
- Unmatched labels (present in source but not target) are silently ignored in the mapping to support partial overlaps.
- The mapper enables "schema evolution" workflows where label standards change across pipeline stages.

---

## 6. System Command Execution

**Entry Point:** `pycemrg.system.CommandRunner`

A robust utility for safely running and logging external shell commands. Provides a consistent interface for executing system processes, capturing their output, and validating results **without using an insecure shell**.

**Instantiation:**
```python
import logging
from pycemrg.system import CommandRunner

# Basic instantiation, uses a default logger
runner = CommandRunner()

# Optionally, inject an application-specific logger for unified log handling
app_logger = logging.getLogger("my_application")
runner = CommandRunner(logger=app_logger)
```

**Methods:**

### `.run()`
Executes a command safely, captures its output, and handles errors.

*   **Signature:** `(cmd: Sequence[Union[str, Path]], expected_outputs: Optional[Sequence[Path]] = None, cwd: Optional[Path] = None, ignore_errors: Optional[Sequence[str]] = None, env: Optional[Dict[str, str]] = None, dry_run: bool = False) -> str`
*   **Args:**
    *   `cmd` (Sequence[str | Path]): A sequence of command parts (e.g., `['docker', 'run', Path('/tmp')]`). Each part is converted to a string. **Never passed to a shell interpreter.**
    *   `expected_outputs` (Optional[Sequence[Path]]): A sequence of `pathlib.Path` objects that are expected to exist after a successful run. If any are missing, raises `FileNotFoundError`.
    *   `cwd` (Optional[Path]): The working directory from which to run the command.
    *   `ignore_errors` (Optional[Sequence[str]]): A sequence of strings. If the command fails but one of these strings is found in stderr, the error is treated as a warning and no exception is raised.
    *   `env` (Optional[Dict[str, str]]): Environment variables dict. If `None`, inherits the current process environment. **If provided, replaces the entire environment** (use with caution or merge with `os.environ`).
    *   `dry_run` (bool): If `True`, log the command that would be run and return immediately. No subprocess is launched, `expected_outputs` is **not** validated, and no exception can be raised. Defaults to `False`.
*   **Returns:**
    *   `str`: The captured stdout from the command, or an empty string when `dry_run` is `True`.
*   **Raises:**
    *   `CommandExecutionError`: If the command returns a non-zero exit code and the error is not in the `ignore_errors` list.
    *   `FileNotFoundError`: If the command completes successfully but an `expected_output` file is missing.

**Example:**
```python
runner = CommandRunner()

# Basic execution
output = runner.run(['ls', '-la', '/tmp'])

# With output validation
runner.run(
    cmd=['convert', 'input.nii', 'output.inr'],
    expected_outputs=[Path('output.inr')]
)

# With error tolerance (some tools write warnings to stderr)
runner.run(
    cmd=['legacy_tool', '--process', 'data.txt'],
    ignore_errors=["WARNING: deprecated flag"]
)

# With custom environment
custom_env = os.environ.copy()
custom_env['CUDA_VISIBLE_DEVICES'] = '0,1'
runner.run(
    cmd=['python', 'train.py'],
    env=custom_env
)

# Preview without executing; returns "" and touches nothing
runner.run(
    cmd=['meshtool', 'extract', 'mesh', '-msh=heart'],
    expected_outputs=[Path('heart_epi.surf')],
    dry_run=True
)
# Logs: [dry-run] Would execute: meshtool extract mesh -msh=heart
```

---

### `.dry_run()`
Logs the command that would be executed, without running it.

*   **Signature:** `(cmd: Sequence[Union[str, Path]]) -> None`
*   **Args:**
    *   `cmd` (Sequence[str | Path]): A sequence of command parts, rendered exactly as `.run()` would render it.
*   **Returns:**
    *   `None`.

**Example:**
```python
runner = CommandRunner()
runner.dry_run(['meshtool', 'extract', 'mesh', '-msh=heart'])
# Logs at INFO: [dry-run] Would execute: meshtool extract mesh -msh=heart
```

Equivalent to `runner.run(cmd, dry_run=True)`, except that `.run()` returns `""`
while `.dry_run()` returns `None`. Prefer `run(..., dry_run=True)` when the call
site is a real invocation being toggled by a flag, so the arguments stay in one
place; prefer `.dry_run()` when you only ever want to preview.

**Design Rationale:**
- **Never uses `shell=True`**: Prevents command injection vulnerabilities.
- **Explicit environment control**: The `env` parameter enables isolated execution (critical for tools like CARPentry that require specific environments).
- **Validation as first-class concern**: `expected_outputs` catches silent failures where a tool exits successfully but produces no output.
- **Dry runs short-circuit before the subprocess**: nothing is launched and no output validation runs, so a dry run can never fail on a missing artifact.

> **Changed in 0.1.3:** `.run()` no longer emits an `Executing command: <cmd>`
> message at INFO before launching. Commands are now logged only via
> `.dry_run()`, or at DEBUG through captured stdout/stderr. Callers that relied
> on seeing the invoked command line in INFO-level logs should pass a logger and
> lower its level, or log the command themselves.

---

**Associated Exception:**

### `pycemrg.system.CommandExecutionError`

A custom exception raised by `CommandRunner.run()` on failure. Subclass of `RuntimeError` providing rich context for programmatic error handling.

*   **Attributes:**
    *   `.returncode` (int): The exit code of the failed command.
    *   `.stdout` (str): The captured standard output from the command.
    *   `.stderr` (str): The captured standard error from the command.

**Example:**
```python
from pycemrg.system import CommandRunner, CommandExecutionError

runner = CommandRunner()

try:
    runner.run(['false'])  # Command that always fails
except CommandExecutionError as e:
    print(f"Command failed with exit code {e.returncode}")
    print(f"Error output: {e.stderr}")
    # Log to monitoring system, retry with different parameters, etc.
```

---

## 7. CARPentry Command Execution

**Entry Point:** `pycemrg.system.CarpRunner`

A specialized runner for executing commands from the CARPentry/openCARP ecosystem. Its primary responsibility is to correctly source the `config.sh` file from a CARPentry installation, setting up the complex environment (`PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, license variables, etc.) before delegating execution to a generic `CommandRunner`.

**Instantiation:**

There are two primary ways to initialize the `CarpRunner`: by providing an explicit path or by using the auto-discovery class method.

**1. Explicit Path (Recommended):**

```python
import logging
from pycemrg.system import CommandRunner, CarpRunner

# A generic CommandRunner is required
runner = CommandRunner()

# Instantiate CarpRunner with the path to the installation's config.sh
carp_runner = CarpRunner(
    runner=runner,
    carp_config_path="/path/to/your/carpentry_bundle/config.sh"
)
```

**2. Auto-Discovery:**

```python
from pycemrg.system import CommandRunner, CarpRunner

runner = CommandRunner()

# Use the classmethod to find the config file in common locations
config_path = CarpRunner.find_installation()

if config_path:
    carp_runner = CarpRunner(runner=runner, carp_config_path=config_path)
else:
    raise RuntimeError("Could not automatically locate CARPentry installation.")
```

**Methods & Properties:**

### `.run()`
Execute a command within the fully configured CARPentry environment.

*   **Signature:** `(cmd: Sequence[Union[str, Path]], expected_outputs: Optional[Sequence[Path]] = None, cwd: Optional[Path] = None, ignore_errors: Optional[Sequence[str]] = None) -> str`
*   **Args:**
    *   `cmd` (Sequence[str | Path]): Command to execute (e.g., `['openCARP', '+F', 'sim.par']`, `['meshtool', 'extract', 'mesh']`).
    *   *Other arguments are passed directly to the underlying `CommandRunner.run()` method.*
*   **Returns:**
    *   `str`: The captured `stdout` from the command.
*   **Raises:**
    *   `CommandExecutionError`: If the command fails.
    *   `CarpEnvironmentError`: If the CARPentry environment fails to load during initialization or reload.
    *   `FileNotFoundError`: If expected outputs are missing after a successful run.

**Example:**
```python
carp = CarpRunner(runner, carp_config_path="/opt/carpentry_bundle/config.sh")

# Run openCARP simulation
carp.run(
    cmd=['openCARP', '+F', 'experiment.par'],
    expected_outputs=[Path('experiment_vm.igb')],
    cwd=Path('/simulations/case_01')
)

# Run meshtool
carp.run(['meshtool', 'extract', 'surface', '-msh=heart', '-surf=epi'])
```

---

### `.carp_env`
A read-only property that returns the loaded CARPentry environment. The environment is lazy-loaded on first access and cached for efficiency.

*   **Type:** `property`
*   **Returns:**
    *   `Dict[str, str]`: A dictionary of all environment variables sourced from `config.sh`.

**Key Variables Sourced:**
- `PATH`: Binaries for `openCARP`, `meshtool`, `meshalyzer`, etc.
- `PYTHONPATH`: `carputils` and related Python modules
- `LD_LIBRARY_PATH`: PETSc and other shared libraries
- `CARPENTRY_LICENSE`: License file location
- `CARPUTILS_SETTINGS`: carputils configuration file
- `OPAL_PREFIX`, `OPAL_BINDIR`, `OPAL_LIBDIR`: MPI settings
- `VIRTUAL_ENV`: Virtual environment paths (if created during installation)

**Example:**
```python
env = carp.carp_env
print(f"CARPentry PATH: {env['PATH']}")
print(f"License file: {env['CARPENTRY_LICENSE']}")
```

---

### `.installation_root`
A read-only property that returns the root directory of the CARPentry installation.

*   **Type:** `property`
*   **Returns:**
    *   `pathlib.Path`: The absolute path to the CARPentry installation directory (the parent directory of `config.sh`).

**Example:**
```python
root = carp.installation_root
meshes_dir = root / "meshes"
examples_dir = root / "carp-examples"
```

---

### `.reload_environment()`
Force reload of the CARPentry environment by re-sourcing `config.sh`.

*   **Signature:** `() -> None`

**Use Cases:**
- The `config.sh` file has been modified externally
- License file has been updated
- Debugging environment issues

**Example:**
```python
# Update license file
shutil.copy("new_license.bin", carp.get_license_path())

# Force reload to pick up changes
carp.reload_environment()
```

---

### `.get_carp_path()`
Get a path relative to the CARPentry installation directory.

*   **Signature:** `(relative_path: str = "") -> Path`
*   **Args:**
    *   `relative_path` (str): Path relative to installation root (default: `""`).
*   **Returns:**
    *   `pathlib.Path`: Absolute path to the requested location.

**Example:**
```python
bin_dir = carp.get_carp_path("bin")
petsc_lib = carp.get_carp_path("petsc/lib")
example_mesh = carp.get_carp_path("meshes/torso/torso")
```

---

### `.validate_command_exists()`
Checks if a specific command (e.g., `openCARP`, `meshtool`) is available in the sourced environment's `PATH`.

*   **Signature:** `(command: str) -> bool`
*   **Args:**
    *   `command` (str): The name of the executable to check. Common commands include:
        - `openCARP`: Main cardiac simulation solver
        - `meshtool`: Mesh manipulation tool
        - `cusummary`: CARPutils summary tool
        - `meshalyzer`: Visualization tool
        - `bench`: Benchmarking tool
*   **Returns:**
    *   `bool`: `True` if command is found and executable, `False` otherwise.

**Example:**
```python
# Validate required tools before workflow
if not carp.validate_command_exists('openCARP'):
    raise RuntimeError("openCARP not found in CARPentry installation")

# Check optional tools
if carp.validate_command_exists('meshalyzer'):
    print("Visualization tools available")
```

---

### `.get_carputils_settings_path()`
Get the path to the carputils `settings.yaml` file.

*   **Signature:** `() -> Optional[Path]`
*   **Returns:**
    *   `Optional[pathlib.Path]`: Path to settings file if `CARPUTILS_SETTINGS` environment variable is set, `None` otherwise.

**Example:**
```python
settings_path = carp.get_carputils_settings_path()
if settings_path and settings_path.exists():
    with open(settings_path) as f:
        config = yaml.safe_load(f)
```

---

### `.get_license_path()`
Get the path to the CARPentry license file.

*   **Signature:** `() -> Optional[Path]`
*   **Returns:**
    *   `Optional[pathlib.Path]`: Path to `license.bin` if `CARPENTRY_LICENSE` environment variable is set, `None` otherwise.

**Example:**
```python
license_path = carp.get_license_path()
if license_path and license_path.exists():
    print(f"License found at: {license_path}")
else:
    raise RuntimeError("CARPentry license not configured")
```

---

### `.find_installation()` (classmethod)
Attempt to locate a CARPentry installation by searching for `config.sh` in common locations.

*   **Signature:** `(search_paths: Optional[Sequence[Path]] = None) -> Optional[Path]`
*   **Type:** `classmethod`
*   **Args:**
    *   `search_paths` (Optional[Sequence[Path]]): A list of directories to search. If `None`, uses default common locations:
        - `~/carpentry_bundle`
        - `~/CARPentry`
        - `~/opencarp`
        - `/opt/carpentry_bundle`
        - `/opt/CARPentry`
        - `/usr/local/carpentry_bundle`
*   **Returns:**
    *   `Optional[pathlib.Path]`: The path to the first `config.sh` file found, or `None` if not found.

**Example:**
```python
# Auto-discover with defaults
config_path = CarpRunner.find_installation()

# Search custom locations
custom_paths = [
    Path("/data/software/carpentry"),
    Path("/shared/tools/opencarp")
]
config_path = CarpRunner.find_installation(custom_paths)
```

---

**Associated Exception:**

### `pycemrg.system.CarpEnvironmentError`

A custom exception raised by `CarpRunner` if it fails to source or validate the CARPentry environment from the `config.sh` file. This can happen if:
- The file is corrupted or incomplete
- The sourcing command fails
- Required environment variables are missing after sourcing

Subclass of `RuntimeError`.

**Example:**
```python
from pycemrg.system import CarpRunner, CarpEnvironmentError

try:
    carp = CarpRunner(runner, carp_config_path="broken_config.sh")
except CarpEnvironmentError as e:
    print(f"Failed to load CARPentry environment: {e}")
    # Fall back to alternative installation or fail gracefully
```

---

## 8. Command-Line Interface (CLI)

For interactive use, the library provides a CLI to perform scaffolding operations.

**Command:** `pycemrg`

**Sub-commands:**

### `init-models`
Creates a `models.yaml` template.

**Usage:**
```bash
pycemrg init-models --output config/models.yaml --force
```

**Options:**
- `--output, -o PATH`: Specify output path (default: `./models.yaml`)
- `--force`: Overwrite if file exists

---

### `init-labels`
Creates a `labels.yaml` template.

**Usage:**
```bash
pycemrg init-labels \
    --output config/labels.yaml \
    --num-labels 10 \
    --num-groups 3 \
    --force
```

**Options:**
- `--output, -o PATH`: Specify output path (default: `./labels.yaml`)
- `--num-labels INT`: Number of placeholder labels (default: 3)
- `--num-groups INT`: Number of placeholder groups (default: 1)
- `--force`: Overwrite if file exists

---

## 9. Advanced Patterns

### Pattern 1: Composing LabelMapper from Multiple Standards

When working with data from multiple sources (e.g., clinical segmentation, research atlas, simulation mesh), use `LabelMapper` to create explicit translation layers:

```python
from pycemrg.data import LabelManager, LabelMapper

# Define three standards
clinical_mgr = LabelManager("clinical_labels.yaml")  # Hospital PACS labels
atlas_mgr = LabelManager("atlas_labels.yaml")        # Research atlas
sim_mgr = LabelManager("simulation_labels.yaml")     # openCARP mesh tags

# Create mappers for each transition
clinical_to_atlas = LabelMapper(clinical_mgr, atlas_mgr)
atlas_to_sim = LabelMapper(atlas_mgr, sim_mgr)

# Orchestrator workflow:
# 1. Load clinical segmentation
seg = load_nifti("patient_seg.nii.gz")

# 2. Translate to atlas standard
atlas_mapping = clinical_to_atlas.get_source_to_target_mapping()
for old_val, new_val in atlas_mapping.items():
    seg[seg == old_val] = new_val

# 3. Further translate to simulation standard
sim_mapping = atlas_to_sim.get_source_to_target_mapping()
for old_val, new_val in sim_mapping.items():
    seg[seg == old_val] = new_val

# 4. Save mesh with correct tags
save_mesh("heart_mesh", seg)
```

**Rationale:** Explicit mapping layers prevent "tag confusion" bugs and make the data provenance traceable.

---

### Pattern 2: OutputManager with ConfigScaffolder in Orchestrators

Use `OutputManager` to enforce consistent naming across all generated files:

```python
from pycemrg.files import OutputManager
from pathlib import Path

def run_segmentation_pipeline(case_id: str, input_image: Path, output_dir: Path):
    # Setup output management
    mgr = OutputManager(output_dir=output_dir, output_prefix=case_id)
    
    # All outputs share the same prefix
    raw_seg_path = mgr.get_path("_raw_segmentation.nii.gz")
    smooth_seg_path = mgr.get_path("_smooth_segmentation.nii.gz")
    mesh_path = mgr.get_path("_heart_mesh.vtk")
    fiber_path = mgr.get_path("_fibers.lon")
    
    # Execute workflow steps
    segment_image(input_image, output=raw_seg_path)
    smooth_segmentation(raw_seg_path, output=smooth_seg_path)
    generate_mesh(smooth_seg_path, output=mesh_path)
    generate_fibers(mesh_path, output=fiber_path)
    
    # All files follow pattern: {case_id}_*.{ext}
    # e.g., patient_042_raw_segmentation.nii.gz
```

**Rationale:** Centralizing path generation prevents typos, ensures consistency, and simplifies batch processing.

---

### Pattern 3: Handling CommandExecutionError in Batch Processing

When processing multiple cases, distinguish between retryable failures and fatal errors:

```python
from pycemrg.system import CommandRunner, CommandExecutionError
import logging

logger = logging.getLogger(__name__)
runner = CommandRunner(logger=logger)

failed_cases = []
retryable_cases = []

for case in case_list:
    try:
        runner.run(
            cmd=['process_case', case.input_path],
            expected_outputs=[case.output_path]
        )
    except CommandExecutionError as e:
        # Check for known retryable errors
        if "out of memory" in e.stderr.lower():
            logger.warning(f"Case {case.id} failed due to memory. Queueing for retry.")
            retryable_cases.append(case)
        elif "cuda" in e.stderr.lower():
            logger.error(f"Case {case.id} failed due to GPU error. Skipping.")
            failed_cases.append((case, e))
        else:
            # Unknown error - fail fast
            raise
    except FileNotFoundError as e:
        # Tool ran but produced no output - likely data issue
        logger.error(f"Case {case.id} produced no output: {e}")
        failed_cases.append((case, e))

# Retry with more resources
for case in retryable_cases:
    runner.run(
        cmd=['process_case', '--memory-limit', '32G', case.input_path],
        expected_outputs=[case.output_path]
    )
```

**Rationale:** Structured exception handling enables robust batch workflows with intelligent retry logic.

---

### Pattern 4: Thread-Safety Considerations

**Important:** Most pycemrg components are **not thread-safe**:

- `ModelManager`: Cache writes are not atomic. Use a single instance per process or protect with locks.
- `LabelManager`/`LabelMapper`: Read-only after initialization, safe for concurrent access.
- `CommandRunner`/`CarpRunner`: Each thread should have its own instance to avoid log interleaving.
- `OutputManager`: Path generation is safe, but filesystem operations (creating directories) are not coordinated.

**Safe Pattern for Parallel Processing:**
```python
from concurrent.futures import ProcessPoolExecutor
from pycemrg.data import LabelManager
from pycemrg.system import CommandRunner

def process_case(case_id: str, labels_config: Path):
    # Each process gets its own instances
    runner = CommandRunner()
    label_mgr = LabelManager(labels_config)
    
    # ... processing logic ...

# Use process pool, not threads
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_case, case_id, labels_config)
        for case_id in case_list
    ]
```

**Rationale:** Process-based parallelism avoids GIL contention and shared-state bugs.

---

## 10. Design Principles Reference

The pycemrg suite follows these architectural principles:

1. **Radical Separation of Concerns**: Libraries provide stateless logic; orchestrators handle I/O and persistence.
2. **Contract-Driven Architecture**: Complex workflows use dataclass contracts to pass data between layers.
3. **Explicit Dependency Injection**: Components receive dependencies at initialization (no globals, no singletons).
4. **Never Derive Paths**: Libraries accept explicit path contracts; they never construct or assume file structures.
5. **Semantic Mapping for Domain Flexibility**: Generic logic accepts semantic maps to decouple algorithms from user-specific schemas.
6. **Tool Wrappers, Not Monoliths**: External tools get thin, focused wrappers exposing Pythonic APIs.
7. **No Premature Abstraction**: Duplication is preferred over the wrong abstraction.

For detailed architectural guidelines, see `pycemrg_suite_guidelines.txt`.

---

## Appendix: Quick Reference

### Common Import Patterns

```python
# Configuration
from pycemrg.files import ConfigScaffolder, OutputManager

# Data Management
from pycemrg.data import LabelManager, LabelMapper
from pycemrg.models import ModelManager

# System Execution
from pycemrg.system import CommandRunner, CarpRunner
from pycemrg.system import CommandExecutionError, CarpEnvironmentError

# Logging
from pycemrg.core import setup_logging
```

### Typical Orchestrator Structure

```python
import logging
from pathlib import Path
from pycemrg.core import setup_logging
from pycemrg.files import OutputManager
from pycemrg.data import LabelManager
from pycemrg.system import CommandRunner

# 1. Setup
setup_logging(log_level=logging.INFO, log_file=Path("pipeline.log"))
logger = logging.getLogger(__name__)

# 2. Initialize managers
output_mgr = OutputManager(output_dir=Path("results"), output_prefix="case_01")
label_mgr = LabelManager(config_path=Path("config/labels.yaml"))
runner = CommandRunner(logger=logger)

# 3. Define paths explicitly
input_path = Path("data/input.nii.gz")
seg_path = output_mgr.get_path("_segmentation.nii.gz")
mesh_path = output_mgr.get_path("_mesh.vtk")

# 4. Execute workflow with validation
runner.run(
    cmd=['segment', str(input_path), str(seg_path)],
    expected_outputs=[seg_path]
)

tags = label_mgr.get_tags_string(["myocardium"])
runner.run(
    cmd=['generate_mesh', str(seg_path), str(mesh_path), '--tags', tags],
    expected_outputs=[mesh_path]
)

logger.info("Pipeline completed successfully")
```

### "Common Patterns and Recipes"

#### Pattern: Pre-flight Input Validation
```python
# Validate all inputs upfront with clear error messages
required = [("input", input_path), ("config", config_path)]
missing = [(name, p) for name, p in required if not p.exists()]
if missing:
    raise FileNotFoundError(
        "Missing files:\n" + "\n".join(f"  {n}: {p}" for n, p in missing)
    )
```

#### Pattern: Preserve Temp Files on Failure
```python
# Context manager for debugging workflows
import tempfile, shutil
from pathlib import Path

class DebugTemp:
    def __init__(self, prefix="debug"):
        self.dir = None
        self.prefix = prefix
    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix=f"{self.prefix}_")
        return Path(self.dir)
    def __exit__(self, exc_type, *_):
        if exc_type is None:
            shutil.rmtree(self.dir)
        else:
            print(f"Debug files: {self.dir}")
        return False
```

#### Pattern: Environment Modification
```python
# Always copy os.environ before modifying
env = os.environ.copy()
env['CUDA_VISIBLE_DEVICES'] = '0'
runner.run(cmd, env=env)

# Never modify os.environ directly (affects entire process)
```

#### Pattern: Domain-Specific Retry Logic
```python
# Example: Retry with exponentially reduced batch size
for batch_size in [32, 16, 8, 4]:
    try:
        runner.run(['train', f'--batch-size={batch_size}'])
        break
    except CommandExecutionError as e:
        if "out of memory" not in e.stderr.lower():
            raise
        logger.warning(f"OOM at batch_size={batch_size}, retrying smaller...")
```