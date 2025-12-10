### **`pycemrg` API Reference: Model & Label Management**

**Overview:**
The pycemrg library provides a decoupled, configuration-driven system for managing common development and research tasks, including Machine Learning models, anatomical labels, and system command execution. The core principle is that the library is stateless and generic; the consuming application provides configuration to direct its behavior.
The typical workflow is:

1. (Optional) Use the ConfigScaffolder or the pycemrg CLI to generate template configuration files.
2. Populate these YAML files with application-specific data.
3. Instantiate the required managers (ModelManager, LabelManager, CommandRunner).
4. Use the manager instances to retrieve model paths, translate label values, and execute external processes.

---

### 1. Configuration Scaffolding

**Entry Point:** `pycemrg.files.ConfigScaffolder`

Programmatically creates template configuration files. This is the recommended first step for a new project.

**Instantiation:**
```python
from pycemrg.files import ConfigScaffolder
scaffolder = ConfigScaffolder()
```

**Methods:**

#### `.create_models_manifest()`
Creates a starter `models.yaml` file with usage examples.

*   **Signature:** `(output_path: Union[str, Path] = "models.yaml", overwrite: bool = False) -> None`
*   **Args:**
    *   `output_path` (str | Path): The location to save the new file. Defaults to `"models.yaml"`.
    *   `overwrite` (bool): If `True`, will overwrite an existing file at the `output_path`. Defaults to `False`.
*   **Raises:**
    *   `FileExistsError`: If the file at `output_path` exists and `overwrite` is `False`.

#### `.create_labels_manifest()`
Creates a starter `labels.yaml` file with usage examples.

*   **Signature:** `(output_path: Union[str, Path] = "labels.yaml", overwrite: bool = False) -> None`
*   **Args:**
    *   `output_path` (str | Path): The location to save the new file. Defaults to `"labels.yaml"`.
    *   `overwrite` (bool): If `True`, will overwrite an existing file at the `output_path`. Defaults to `False`.
*   **Raises:**
    *   `FileExistsError`: If the file at `output_path` exists and `overwrite` is `False`.

---

### 2. Model Management

**Entry Point:** `pycemrg.models.manager.ModelManager`

Manages downloading, caching, and providing local filesystem paths to ML models defined in a manifest.

**Instantiation:**
```python
from pycemrg.models.manager import ModelManager
from pathlib import Path

# The path to your application's models.yaml is required.
model_manager = ModelManager(manifest_path=Path("path/to/your/models.yaml"))

# Optionally, specify a custom cache directory.
# model_manager = ModelManager(
#     manifest_path=Path("path/to/your/models.yaml"),
#     cache_dir=Path("/tmp/my-app-cache")
# )
```

**Methods:**

#### `.get_model_path()`
The primary method. It returns the local path to a model's weights, handling download, verification, and unzipping as needed. The operation is idempotent; subsequent calls for the same model will return the cached path instantly.

*   **Signature:** `(model_name: str, version: str = 'default') -> Path`
*   **Args:**
    *   `model_name` (str): The logical name of the model (a top-level key in `models.yaml`).
    *   `version` (str): The specific version to retrieve. If not provided, uses the `default` version specified in the manifest.
*   **Returns:**
    *   `pathlib.Path`: A resolved, absolute path to the ready-to-use model file.
*   **Raises:**
    *   `FileNotFoundError`: If the provided `manifest_path` does not exist.
    *   `KeyError`: If the `model_name` or `version` is not found in the manifest.
    *   `ValueError`: If the manifest entry for the model is malformed (e.g., missing `unzipped_target_path`).
    *   `RuntimeError`: If a network, hashing, or unzipping error occurs during processing.

---

### 3. Label Management

**Entry Point:** `pycemrg.data.labels.LabelManager`

Manages translations between human-readable label names, groups, and their corresponding integer values based on a label manifest.

**Instantiation:**
```python
from pycemrg.data.labels import LabelManager
from pathlib import Path

# The path to your application's labels.yaml is required.
label_manager = LabelManager(config_path=Path("path/to/your/labels.yaml"))
```
**Methods:**

#### `.get_value()`
Translates a single label name to its integer value.

*   **Signature:** `(name: str) -> int`
*   **Args:**
    *   `name` (str): The human-readable label name (e.g., `"left_ventricle"`).
*   **Returns:**
    *   `int`: The corresponding integer value.
*   **Raises:**
    *   `KeyError`: If `name` is not defined in the manifest's `labels` section.

#### `.get_name()`
Translates an integer value back to its human-readable name.

*   **Signature:** `(value: int) -> str`
*   **Args:**
    *   `value` (int): The integer value of the label.
*   **Returns:**
    *   `str`: The corresponding human-readable name.
*   **Raises:**
    *   `KeyError`: If `value` is not defined in the manifest's `labels` section.

#### `.get_values_from_names()`
Translates a list of strings into a sorted, unique list of integer label values. The input list can contain individual label names, group names, or numbers as strings.

*   **Signature:** `(names: list[str]) -> list[int]`
*   **Args:**
    *   `names` (list[str]): A list of strings to translate. Can include keys from `labels`, keys from `groups`, or numeric strings (e.g., `['blood_pools', 'structure_a', '5']`).
*   **Returns:**
    *   `list[int]`: A sorted list of unique integer values corresponding to the input names.
*   **Raises:**
    *   `KeyError`: If any name in the list is not a valid label, group, or digit.

### 4. System Command Execution

**Entry point:** `pycemrg.system.CommandRunner`

A robust utility for safely running and logging external shell commands. It provides a consistent interface for executing system processes, capturing their output, and validating results without using an insecure shell.

```python 
import logging
from pycemrg.system import CommandRunner

# Basic instantiation, uses a default logger
runner = CommandRunner()

# Optionally, inject an application-specific logger for unified log handling
app_logger = logging.getLogger("my_application")
runner = CommandRunner(logger=app_logger)
```

**Methods**:

`.run()`

Executes a command safely, captures its output, and handles errors.
* **Signature**: `(cmd: Sequence[Union[str, Path]], expected_outputs: Optional[Sequence[Path]] = None, cwd: Optional[Path] = None, ignore_errors: Optional[Sequence[str]] = None) -> str`
* **Args**:
  * `cmd` (Sequence[str | Path]): A sequence of command parts (e.g., `['docker', 'run', Path('/tmp')]`). Each part is converted to a string.
  * `expected_outputs` (Optional[Sequence[Path]]): A sequence of `pathlib.Path` objects that are expected to exist after a successful run.
  * `cwd` (Optional[Path]): The working directory from which to run the command.
  * `ignore_errors` (Optional[Sequence[str]]): A sequence of strings. If the command fails but one of these strings is found in stderr, the error is treated as a warning and no exception is raised.
* **Returns**:
  * `str`: The captured stdout from the command.
* **Raises**:
  * `pycemrg.system.CommandExecutionError`: If the command returns a non-zero exit code and the error is not in the ignore_errors list.
  * `FileNotFoundError`: If the command completes successfully but an expected_output file is missing.

**Associated Exception**:

`pycemrg.system.CommandExecutionError`

A custom exception raised by `CommandRunner.run()` on failure. It is a subclass of RuntimeError and provides rich context for programmatic error handling.

* **Attributes**:
  * `.returncode` (int): The exit code of the failed command.
  * `.stdout` (str): The captured standard output from the command.
  * `.stderr` (str): The captured standard error from the command.


---

### 5. Command-Line Interface (CLI)

For interactive use, the library provides a CLI to perform scaffolding.

*   **Command:** `pycemrg`
*   **Sub-commands:**
    *   `pycemrg init-models`: Creates a `models.yaml` template.
        *   `--output, -o`: Specify output path.
        *   `--force`: Overwrite if file exists.
    *   `pycemrg init-labels`: Creates a `labels.yaml` template.
        *   `--output, -o`: Specify output path.
        *   `--force`: Overwrite if file exists.