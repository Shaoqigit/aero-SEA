# SEA Engine Architecture

## Overview

SEA Engine is a vibroacoustic simulation software for engineering applications, built on top of Pyva. It provides a comprehensive framework for Statistical Energy Analysis (SEA) with an engineering-focused interface.

## Based On

- **Pyva**: Python toolbox for vibroacoustics (https://github.com/minipief/pyva)
- **Reference**: "Vibroacoustic Simulation: An Introduction to Statistical Energy Analysis and Hybrid Methods" by A. Peiffer (Wiley, 2022)

## Architecture Principles

1. **Modularity**: Separate concerns into distinct modules (core, gui, templates, utils)
2. **Extensibility**: Easy to add new material models, element types, and analysis types
3. **User-Friendly**: Engineering-focused API with templates for common scenarios
4. **Visualization**: Built-in result visualization and export capabilities

## Project Structure

```
sea_engine/
├── __init__.py              # Main package exports
├── core/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   └── engine.py           # Main SEA engine (wraps Pyva)
├── models/
│   ├── __init__.py
│   └── project.py          # Project management
├── gui/
│   ├── __init__.py
│   └── main_window.py      # Main application window
├── templates/
│   ├── __init__.py         # Pre-built simulation templates
│   └── ...
├── utils/
│   ├── __init__.py         # Utility functions
│   └── ...
└── tests/
    └── __init__.py
```

## Core Components

### 1. SEAEngine (`core/engine.py`)

Main computation engine that wraps Pyva functionality:

- **FrequencyRange**: Frequency axis definition for analysis
- **MaterialDefinition**: Material properties for SEA systems
- **StructuralElement**: Plate, beam, and shell structures
- **AcousticSpace**: Acoustic cavities and rooms
- **Junction**: Coupling between subsystems (area, line, semi-infinite)
- **Load**: Power, force, and pressure loads

Key methods:
- `add_structural_element()`: Add structural components
- `add_acoustic_space()`: Add acoustic cavities
- `add_junction()`: Define coupling between systems
- `add_load()`: Apply excitation
- `build_model()`: Construct Pyva HybridModel
- `solve()`: Execute SEA solution
- `get_energy_results()`: Retrieve computed results

### 2. SEAProject (`models/project.py`)

Project management class:

- Stores all model components (materials, structures, spaces, junctions, loads)
- Handles project serialization (JSON format)
- Manages analysis settings
- Provides save/load functionality

### 3. Configuration (`core/config.py`)

Centralized configuration management:

- Solver settings (frequency range, bands, convergence)
- GUI settings (theme, window size)
- Export settings (formats, directories)

### 4. Templates (`templates/`)

Pre-built simulation templates for common scenarios:

- **BuildingAcousticTemplate**: Two rooms separated by a wall
- **VehicleInteriorTemplate**: Vehicle cabin noise analysis
- **EquipmentEnclosureTemplate**: Equipment box enclosures

### 5. Utilities (`utils/`)

Helper functions and data:

- **FrequencyConverter**: Hz ↔ angular frequency conversion
- **ResultFormatter**: SPL, transmission loss, energy formatting
- **UnitConverter**: Unit conversions (Pa, mm, kg, etc.)
- **MaterialLibrary**: Pre-defined engineering materials (steel, aluminum, concrete, etc.)
- **FileManager**: File operations and validation

## Pyva Integration

SEA Engine wraps Pyva's core classes:

| Pyva Component | SEA Engine Equivalent |
|---------------|----------------------|
| `matC.Fluid` | `MaterialDefinition(fluid)` |
| `matC.IsoMat` | `MaterialDefinition(solid)` |
| `stPC.PlateProp` | `StructuralElement.to_pyva_property()` |
| `ac3Dsys.RectangularRoom` | `AcousticSpace.to_pyva_system()` |
| `con.AreaJunction` | `Junction(junction_type="area")` |
| `con.LineJunction` | `Junction(junction_type="line")` |
| `mds.HybridModel` | `SEAEngine.model` |

## Analysis Workflow

```
1. Create Project
   ↓
2. Define Frequency Range
   ↓
3. Add Materials
   ↓
4. Add Structural Elements (plates, beams)
   ↓
5. Add Acoustic Spaces (rooms, cavities)
   ↓
6. Define Junctions (couplings)
   ↓
7. Apply Loads (power, force, pressure)
   ↓
8. Build Model (converts to Pyva)
   ↓
9. Solve (SEA matrix solution)
   ↓
10. Post-process Results
```

## Usage Example

```python
from sea_engine import SEAProject
from sea_engine.core.engine import (
    MaterialDefinition, StructuralElement,
    AcousticSpace, Junction, Load
)
from sea_engine.templates import BuildingAcousticTemplate

# Create project
project = SEAProject()
project.metadata.name = "Building Acoustic Example"
project.set_frequency_range(100, 5000, "third_octave")

# Use template for two rooms
template = BuildingAcousticTemplate.create_two_rooms(
    room1_dims=(3, 4, 2.5),    # Lx, Ly, Lz
    room2_dims=(5, 4, 2.5),
    wall_thickness=0.05,       # 5cm concrete wall
    wall_material="concrete"
)

# Add components from template
for mat in template["materials"]:
    project.add_material(mat)
for struct in template["structures"]:
    project.add_structure(struct)
for space in template["acoustic_spaces"]:
    project.add_acoustic_space(space)

# Add coupling junction
wall = project.get_structure("wall")
room1 = project.get_acoustic_space("room1")
room2 = project.get_acoustic_space("room2")

junction = Junction(
    name="wall_junction",
    junction_type="area",
    systems=(room1, wall, room2)
)
project.add_junction(junction)

# Add power load
load = Load(
    name="source",
    load_type="power",
    system_id=room1.system_id,
    magnitude=0.001  # 1mW
)
project.add_load(load)

# Run analysis
project.run_analysis()

# Get results
results = project.get_results()
print(results['energy'])
```

## Dependencies

- **pyva**: Vibroacoustic simulation library
- **numpy**: Numerical computing
- **scipy**: Scientific computing
- **matplotlib**: Visualization (for GUI)
- **PyQt6/PySide6**: GUI framework

## Next Steps

1. **GUI Implementation**: Full Qt-based interface with:
   - 3D model visualization
   - Material library browser
   - Template wizard
   - Result plotting

2. **Advanced Features**:
   - Parameter optimization
   - Monte Carlo analysis
   - Sensitivity analysis

3. **Export Options**:
   - CSV/Excel export
   - PDF report generation
   - HDF5 data format

## License

LGPL-2.1 (same as Pyva)
