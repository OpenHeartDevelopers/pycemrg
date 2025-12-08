### **`pycemrg` API Reference: Model & Label Management**

**Overview:**
The `pycemrg` library provides a decoupled, configuration-driven system for managing Machine Learning models and anatomical labels. The core principle is that the library is stateless and generic; the consuming application provides YAML files to configure its behavior.

The typical workflow is:
1.  (Optional) Use the `ConfigScaffolder` or the `pycemrg` CLI to generate template `models.yaml` and `labels.yaml` files.
2.  Populate these YAML files with application-specific data.
3.  Instantiate `ModelManager` and `LabelManager` with the paths to these configuration files.
4.  Use the manager instances to retrieve model paths and translate label values.

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

---

### 4. Command-Line Interface (CLI)

For interactive use, the library provides a CLI to perform scaffolding.

*   **Command:** `pycemrg`
*   **Sub-commands:**
    *   `pycemrg init-models`: Creates a `models.yaml` template.
        *   `--output, -o`: Specify output path.
        *   `--force`: Overwrite if file exists.
    *   `pycemrg init-labels`: Creates a `labels.yaml` template.
        *   `--output, -o`: Specify output path.
        *   `--force`: Overwrite if file exists.