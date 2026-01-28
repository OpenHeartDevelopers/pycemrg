# pycemrg

Core utilities for cardiac medical image analysis workflows.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

`pycemrg` provides a stateless, configuration-driven foundation for building reproducible medical imaging pipelines. It handles common tasks like model versioning, anatomical label translation, path management, and safe command execution—letting you focus on scientific workflows rather than boilerplate.

**Design Philosophy:** Libraries provide stateless logic; orchestrators handle I/O. All paths are explicit, no magic configuration, no hidden state.

## Features

- **Model Management**: Download, cache, and version ML models with SHA256 integrity verification
- **Label Management**: Translate between human-readable anatomical names and integer segmentation values
- **Path Management**: Generate consistent output paths with configurable prefix/suffix patterns
- **Command Execution**: Safely run external tools (meshtool, openCARP) with validation and error handling
- **Configuration Scaffolding**: Generate template YAML configs via CLI or programmatic API
- **CARPentry Integration**: Specialized runner for openCARP ecosystem with environment isolation

## Installation
```bash
pip install pycemrg
```

## Quick Start

### Generate Configuration Templates
```bash
# Create a labels configuration template
pycemrg init-labels --output config/labels.yaml --num-labels 10

# Create a models configuration template
pycemrg init-models --output config/models.yaml
```

### Manage Anatomical Labels
```python
from pycemrg.data import LabelManager

# Load your anatomical label definitions
labels = LabelManager("config/labels.yaml")

# Translate between names and integer values
lv_value = labels.get_value("LV_myo")  # Returns: 2

# Resolve groups (including recursive definitions)
chamber_values = labels.get_values_from_names(["ventricles", "atria"])
# Returns: [2, 3, 4, 5] (sorted, deduplicated)

# Generate tag strings for command-line tools
tags = labels.get_tags_string(["LV_myo", "RV_myo"])  # Returns: "2,3"
```

**Example `labels.yaml`:**
```yaml
labels:
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
```

### Manage ML Models
```python
from pycemrg.models import ModelManager

# Initialize with your models manifest
models = ModelManager("config/models.yaml")

# Get path to model weights (downloads/caches automatically)
model_path = models.get_model_path("segmentation_model")
# First call: Downloads, verifies SHA256, extracts → ~/.cache/pycemrg/...
# Subsequent calls: Returns cached path instantly

# Use specific version
legacy_path = models.get_model_path("segmentation_model", version="v1.0")
```

**Example `models.yaml`:**
```yaml
segmentation_model:
  default: v2.0
  versions:
    v2.0:
      url: "https://example.com/models/seg_v2.0.zip"
      sha256: "abc123..."
      unzipped_target_path: "checkpoints/model.pth"
```

### Execute Commands Safely
```python
from pycemrg.system import CommandRunner

runner = CommandRunner()

# Run with output validation
runner.run(
    cmd=['meshtool', 'extract', 'mesh', '-msh=heart'],
    expected_outputs=[Path('heart_epi.surf')]
)

# Handle tools that write warnings to stderr
runner.run(
    cmd=['legacy_tool', '--process', 'data.txt'],
    ignore_errors=["WARNING: deprecated flag"]
)
```

## Documentation

- [API Reference](docs/API_reference.md) - Complete API documentation
- [Architecture Guidelines](docs/pycemrg_suite_guidelines.txt) - Design principles and patterns

## Related Packages

`pycemrg` is the stable core of a suite of cardiac imaging tools:

- **pycemrg-image-analysis**: Medical image processing workflows (segmentation, meshing)
- **pycemrg-model-creation**: Cardiac mesh generation and UVC coordinate systems
- **pycemrg-interpolation**: Functional autoencoder-based image interpolation

## Development

### Local Installation
```bash
# Clone and install in editable mode
git clone https://github.com/YOUR-ORG/pycemrg.git
cd pycemrg
pip install -e ".[dev]"

# Run tests
pytest tests/
```

### Contributing

This library follows strict architectural principles:
- **Stateless logic**: No hidden state, all dependencies injected
- **Contract-driven**: Complex workflows use dataclass contracts
- **Path-agnostic**: Libraries never derive paths; orchestrators provide them explicitly

See [Architecture Guidelines](docs/pycemrg_suite_guidelines.txt) for details.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Citation

If you use `pycemrg` in your research, please cite:
```bibtex
@software{pycemrg2025,
  title = {pycemrg: Core utilities for cardiac medical image analysis},
  author = {[Your Name]},
  year = {2025},
  url = {https://github.com/YOUR-ORG/pycemrg}
}
```