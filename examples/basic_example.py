"""
SEA Engine Example - Basic Building Acoustic Analysis

This example demonstrates how to use SEA Engine for a simple
wall-room acoustic simulation using Statistical Energy Analysis.
"""

import numpy as np
from pathlib import Path

# Import SEA Engine components
from sea_engine import SEAProject
from sea_engine.core.engine import (
    MaterialDefinition, StructuralElement,
    AcousticSpace, Junction, Load, FrequencyRange
)
from sea_engine.utils import MaterialLibrary


def create_wall_room_example():
    """
    Create a wall-room acoustic model.

    Room (source) <-> Concrete Wall
    """

    print("=" * 60)
    print("SEA Engine - Wall-Room Acoustic Example")
    print("=" * 60)

    # Step 1: Create project
    project = SEAProject()
    project.metadata.name = "Wall-Room Acoustic"
    project.metadata.description = "Example: Sound transmission through wall"
    project.metadata.author = "Engineering Team"

    print("\n[1] Project created")

    # Step 2: Set frequency range
    project.set_frequency_range(
        f_min=100,      # 100 Hz
        f_max=5000,     # 5 kHz
        band_type="third_octave"
    )
    print("[2] Frequency range set: 100 Hz - 5 kHz (third octave)")

    # Step 3: Add materials
    # Concrete wall material
    concrete = MaterialDefinition(
        name="concrete",
        material_type="solid",
        density=1250.0,           # kg/m³
        youngs_modulus=3.8e9,     # Pa
        poisson_ratio=0.33,
        loss_factor=0.03
    )
    project.add_material(concrete)
    print("[3] Material added: concrete")

    # Step 4: Add structural elements
    wall = StructuralElement(
        name="concrete_wall",
        element_type="plate",
        dimensions={
            "thickness": 0.05,    # 5 cm
            "Lx": 4.0,            # Width
            "Ly": 2.5             # Height
        },
        material=concrete,
        damping_loss_factor=0.03
    )
    wall_id = project.add_structure(wall)
    print(f"[4] Structural element added: concrete wall (ID={wall_id})")

    # Step 5: Add acoustic space (room)
    room = AcousticSpace(
        name="room",
        dimensions=(3.0, 4.0, 2.5),  # Lx, Ly, Lz
        absorption_area=8.0,          # m²
        damping_type=["surface"]
    )
    room_id = project.add_acoustic_space(room)
    print(f"[5] Acoustic space added: room (ID={room_id})")

    # Step 6: Add junction (coupling) - 2 systems only for Pyva
    # For more complex models, add multiple junctions
    junction = Junction(
        name="wall_room_junction",
        junction_type="area",
        systems=(room, wall)  # room-wall coupling
    )
    project.add_junction(junction)
    print("[6] Junction added: area coupling between room and wall")

    # Step 7: Add load (power input to room)
    power_load = Load(
        name="source_power",
        load_type="power",
        system_id=room_id,
        magnitude=0.001  # 1 mW
    )
    project.add_load(power_load)
    print("[7] Load added: 1 mW power input to room")

    # Step 8: Run analysis
    print("\n[8] Building model and solving...")
    if project.run_analysis():
        print("    ✓ Analysis completed successfully!")
    else:
        print("    ✗ Analysis failed!")
        return None

    # Step 9: Get and display results
    print("\n[9] Results:")
    results = project.get_results()

    if results:
        energy = results.get('energy')
        if energy:
            print(f"    Energy data shape: {energy.ydata.shape}")
            print(f"    Energy DOF: {energy.dof}")

        result = results.get('result')
        if result:
            print(f"    Result data shape: {result.ydata.shape}")

    # Step 10: Save project
    output_path = Path("./examples/output")
    output_path.mkdir(parents=True, exist_ok=True)
    project.save(output_path / "wall_room.seaproj")
    print(f"\n[10] Project saved to: {output_path / 'wall_room.seaproj'}")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)

    return project


def create_material_library_example():
    """Demonstrate using the built-in material library."""

    print("\n" + "=" * 60)
    print("Material Library Example")
    print("=" * 60)

    # List available materials
    materials = MaterialLibrary.list_materials()
    print(f"\nAvailable materials ({len(materials)}):")
    for mat_name in materials:
        print(f"  - {mat_name}")

    # Get specific material
    steel = MaterialLibrary.get_material("steel")
    if steel:
        print(f"\nSteel properties:")
        print(f"  Density: {steel['density']} kg/m³")
        print(f"  Young's Modulus: {steel['youngs_modulus']/1e9:.0f} GPa")
        print(f"  Poisson Ratio: {steel['poisson_ratio']}")

    return steel


def demonstrate_frequency_conversion():
    """Demonstrate frequency utility functions."""

    print("\n" + "=" * 60)
    print("Frequency Conversion Example")
    print("=" * 60)

    from sea_engine.utils import FrequencyConverter

    # Third octave bands
    freq_hz = FrequencyConverter.get_third_octave_bands(100, 5000)
    print(f"\nThird octave bands (100 Hz - 5 kHz):")
    print(f"  Number of bands: {len(freq_hz)}")
    print(f"  First 5 bands: {freq_hz[:5]} Hz")
    print(f"  Last 5 bands: {freq_hz[-5:]} Hz")

    # Convert to angular frequency
    freq_rad = FrequencyConverter.hz_to_angular(freq_hz)
    print(f"\nConverted to angular frequency:")
    print(f"  First band: {freq_rad[0]:.1f} rad/s")

    # Convert back
    freq_hz_back = FrequencyConverter.angular_to_hz(freq_rad)
    print(f"  Back to Hz (verification): {np.allclose(freq_hz, freq_hz_back)}")


if __name__ == "__main__":
    # Run examples
    project = create_wall_room_example()

    steel = create_material_library_example()

    demonstrate_frequency_conversion()

    print("\n✓ All examples completed successfully!")
