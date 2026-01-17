# SEA Engine

**Statistical Energy Analysis (SEA) Software for Engineering Applications**

SEA Engine is a vibroacoustic simulation software built on top of Pyva, designed for engineering applications in building acoustics, vehicle noise, and industrial noise control.

## Based On

- **Pyva**: Python toolbox for vibroacoustics (https://github.com/minipief/pyva)
- **Reference**: "Vibroacoustic Simulation: An Introduction to Statistical Energy Analysis and Hybrid Methods" by A. Peiffer (Wiley, 2022)

## Features

- **SEA Analysis**: Full Statistical Energy Analysis for mid-to-high frequency vibroacoustics
- **Material Library**: Pre-defined materials (steel, aluminum, concrete, glass, etc.)
- **Engineering API**: Pythonic interface designed for engineering workflows
- **Result Processing**: Built-in utilities for SPL, transmission loss, and energy calculations
- **Project Management**: Save/load projects in JSON format
- **Frequency Utilities**: Third octave band generation, Hz ↔ angular conversion

## Installation

```bash
# Create conda environment (recommended)
conda create -n sea-pyva python=3.12
conda activate sea-pyva

# Install dependencies
conda install -y scipy numpy matplotlib pandas --channel conda-forge

# Install Pyva from GitHub
cd /tmp
git clone https://github.com/minipief/pyva.git
cd pyva
pip install -e .

# Install SEA Engine
cd /path/to/sea_pyva
pip install -e .
```

## Quick Start

```python
from sea_engine import SEAProject
from sea_engine.core.engine import MaterialDefinition, StructuralElement, AcousticSpace, Junction, Load

# Create project
project = SEAProject()
project.set_frequency_range(100, 5000, "third_octave")

# Add materials
concrete = MaterialDefinition(
    name="concrete",
    material_type="solid",
    density=1250.0,
    youngs_modulus=3.8e9,
    poisson_ratio=0.33,
    loss_factor=0.03
)
project.add_material(concrete)

# Add structures (wall)
wall = StructuralElement(
    name="wall",
    element_type="plate",
    dimensions={"thickness": 0.05, "Lx": 4.0, "Ly": 2.5},
    material=concrete,
    damping_loss_factor=0.03
)
project.add_structure(wall)

# Add acoustic space (room)
room = AcousticSpace(
    name="room",
    dimensions=(3.0, 4.0, 2.5),
    absorption_area=8.0
)
project.add_acoustic_space(room)

# Add junction (2-system coupling: room-wall)
junction = Junction(
    name="wall_room_junction",
    junction_type="area",
    systems=(room, wall)
)
project.add_junction(junction)

# Add load
load = Load(
    name="source",
    load_type="power",
    system_id=room.system_id,
    magnitude=0.001
)
project.add_load(load)

# Run analysis
project.run_analysis()

# Get results
results = project.get_results()
print(f"Energy shape: {results['energy'].ydata.shape}")
```

## Project Structure

```
sea_engine/
├── __init__.py              # Main package exports
├── core/
│   ├── config.py           # Configuration management
│   └── engine.py           # Main SEA engine (wraps Pyva)
├── models/
│   └── project.py          # Project management
├── gui/
│   └── main_window.py      # Main application window (placeholder)
├── templates/
│   └── __init__.py         # Pre-built simulation templates
├── utils/
│   ├── __init__.py         # Utility functions
│   └── export.py           # Result export (CSV, JSON, PNG, PDF)
└── tests/
    └── __init__.py
```

## Utilities

```python
from sea_engine.utils import MaterialLibrary, FrequencyConverter

# Get material properties
steel = MaterialLibrary.get_material("steel")
print(f"Steel density: {steel['density']} kg/m³")

# Third octave bands
freq_hz = FrequencyConverter.get_third_octave_bands(100, 5000)
print(f"Number of bands: {len(freq_hz)}")

# Convert frequencies
freq_rad = FrequencyConverter.hz_to_angular(freq_hz)
freq_back = FrequencyConverter.angular_to_hz(freq_rad)
```

## Examples

Run the examples:

```bash
python examples/basic_example.py
```

Available materials:
- steel, aluminum, concrete, glass, plywood, air, fiberglass

## Documentation

- [Architecture](ARCHITECTURE.md) - Detailed software architecture
- [Pyva Documentation](https://pyva.eu) - Pyva library documentation
- [SEA Theory](https://docpeiffer.com/statistical-energy-analysis-sea/) - Introduction to SEA

## Requirements

- Python 3.8+
- numpy >= 1.20.0
- scipy >= 1.7.0
- matplotlib >= 3.5.0
- pandas >= 1.4.0
- pyva (from GitHub: minipief/pyva)

## License

LGPL-2.1 (same as Pyva)

## Author

Engineering Team

## References

1. A. Peiffer, "Vibroacoustic Simulation: An Introduction to Statistical Energy Analysis and Hybrid Methods", Wiley, 2022
2. Lyon, R.H., "Statistical Energy Analysis of Dynamical Systems in Acoustics", MIT Press, 1995
