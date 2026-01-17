# SEA Engine Setup Guide

## Environment Setup

### 1. Activate the conda environment

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate sea-pyva
```

### 2. Install required dependencies

```bash
# Install numpy, scipy, matplotlib, pandas (if not already installed)
pip install numpy scipy matplotlib pandas

# Install Pyva from GitHub
cd /tmp/pyva
pip install -e .
```

### 3. Verify installation

```bash
python -c "
import pyva
import numpy as np
import scipy

print('Pyva imported successfully')
print('NumPy version:', np.__version__)
print('SciPy version:', scipy.__version__)
"
```

## Project Structure

```
sea_pyva/
├── README.md              # Main documentation
├── ARCHITECTURE.md        # Detailed architecture
├── SETUP.md              # This setup guide
├── requirements.txt      # Dependencies
├── examples/
│   └── basic_example.py  # Basic usage example
└── sea_engine/
    ├── __init__.py       # Main package
    ├── core/
    │   ├── __init__.py
    │   ├── config.py     # Configuration management
    │   └── engine.py     # Main SEA engine
    ├── models/
    │   ├── __init__.py
    │   └── project.py    # Project management
    ├── gui/
    │   ├── __init__.py
    │   └── main_window.py
    ├── templates/
    │   └── __init__.py   # Pre-built templates
    ├── utils/
    │   ├── __init__.py   # Utilities
    │   └── export.py     # Export functionality
    └── tests/
        └── __init__.py
```

## Quick Start

```python
from sea_engine import SEAProject
from sea_engine.core.engine import (
    MaterialDefinition, StructuralElement,
    AcousticSpace, Junction, Load
)
from sea_engine.templates import BuildingAcousticTemplate

# Create project
project = SEAProject()
project.set_frequency_range(100, 5000, "third_octave")

# Use template for two rooms
template = BuildingAcousticTemplate.create_two_rooms(
    room1_dims=(3, 4, 2.5),
    room2_dims=(5, 4, 2.5),
    wall_thickness=0.05
)

# Add components
for mat in template["materials"]:
    project.add_material(mat)
for struct in template["structures"]:
    project.add_structure(struct)
for space in template["acoustic_spaces"]:
    project.add_acoustic_space(space)

# Add coupling
wall = project.get_structure("wall")
room1 = project.get_acoustic_space("room1")
room2 = project.get_acoustic_space("room2")

junction = Junction(
    name="wall_junction",
    junction_type="area",
    systems=(room1, wall, room2)
)
project.add_junction(junction)

# Add load and solve
load = Load(
    name="source",
    load_type="power",
    system_id=room1.system_id,
    magnitude=0.001
)
project.add_load(load)
project.run_analysis()

# Get results
results = project.get_results()
print(results['energy'])
```

## Common Issues

### Pyva import errors

If you get import errors for pyva, make sure it's installed correctly:

```bash
cd /tmp/pyva
pip install -e .
```

### Scipy not found

If scipy is not found, install it:

```bash
pip install scipy
```

### NumPy version conflicts

If you have version conflicts, try:

```bash
pip install --upgrade numpy scipy
```

## Dependencies

- Python 3.8+
- numpy >= 1.20.0
- scipy >= 1.7.0
- matplotlib >= 3.5.0
- pandas >= 1.4.0
- pyva (from GitHub: minipief/pyva)
