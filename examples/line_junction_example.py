"""
SEA Engine Example - Line Junction Analysis

This example demonstrates how to use line junctions for edge couplings
in building acoustic simulations (e.g., perpendicular walls meeting at corners).
"""

import numpy as np
from pathlib import Path

# Import SEA Engine components
from sea_engine import SEAProject
from sea_engine.core.engine import (
    MaterialDefinition, StructuralElement,
    AcousticSpace, Junction, Load
)
from sea_engine.templates import JunctionFactory


def create_line_junction_example():
    """
    Create a model with line junctions for wall corner couplings.
    
    This example shows:
    1. Room with wall using area junction
    2. Two walls connected using line junction (perpendicular corner)
    
    Room (source) <-> Wall 1 (area junction)
    Wall 1 <-> Wall 2 (line junction - perpendicular walls)
    """
    
    print("=" * 60)
    print("SEA Engine - Line Junction Example")
    print("=" * 60)
    
    # Step 1: Create project
    project = SEAProject()
    project.metadata.name = "Line Junction Analysis"
    project.metadata.description = "Example: Wall corner with line junction coupling"
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
    
    # Step 4: Add structural elements (two walls meeting at corner)
    wall1 = StructuralElement(
        name="wall_horizontal",
        element_type="plate",
        dimensions={
            "thickness": 0.05,    # 5 cm
            "Lx": 4.0,            # Width
            "Ly": 2.5             # Height
        },
        material=concrete,
        damping_loss_factor=0.03
    )
    wall1_id = project.add_structure(wall1)
    print(f"[4a] Structural element added: wall_horizontal (ID={wall1_id})")
    
    wall2 = StructuralElement(
        name="wall_vertical",
        element_type="plate",
        dimensions={
            "thickness": 0.05,    # 5 cm
            "Lx": 2.5,            # Width (corner height)
            "Ly": 3.0             # Height
        },
        material=concrete,
        damping_loss_factor=0.03
    )
    wall2_id = project.add_structure(wall2)
    print(f"[4b] Structural element added: wall_vertical (ID={wall2_id})")
    
    # Step 5: Add acoustic space (single room)
    room = AcousticSpace(
        name="room",
        dimensions=(3.0, 4.0, 2.5),
        absorption_area=8.0,
        damping_type=["surface"]
    )
    room_id = project.add_acoustic_space(room)
    print(f"[5] Acoustic space added: room (ID={room_id})")
    
    # Step 6: Add junctions
    
    # Area junction: room <-> wall1 (main coupling)
    # Pyva expects acoustic system first, then structural
    junction1 = Junction(
        name="room_wall1",
        junction_type="area",
        systems=(room, wall1),  # Acoustic first, then structural
        area=10.0  # 10 m² coupling area
    )
    project.add_junction(junction1)
    print("[6a] Junction added: area coupling (wall1 <-> room)")
    
    # Line junction: wall1 <-> wall2 (corner connection)
    # This is the key feature - edge coupling between perpendicular walls
    junction2 = JunctionFactory.create_perpendicular_wall_junction(
        name="wall_corner",
        wall1=wall1,
        wall2=wall2,
        length=2.5  # Junction length matching wall height
    )
    project.add_junction(junction2)
    print("[6b] Junction added: line coupling (wall1 <-> wall2) at corner")
    
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
        print("    Analysis completed successfully!")
    else:
        print("    Analysis failed!")
        return None
    
    # Step 9: Get and display results
    print("\n[9] Results:")
    results = project.get_results()
    
    if results:
        energy = results.get('energy')
        if energy:
            print(f"    Energy data shape: {energy.ydata.shape}")
            print(f"    Energy DOF: {energy.dof}")
    
    # Step 10: Save project
    output_path = Path("./examples/output")
    output_path.mkdir(parents=True, exist_ok=True)
    project.save(output_path / "line_junction.seaproj")
    print(f"\n[10] Project saved to: {output_path / 'line_junction.seaproj'}")
    
    print("\n" + "=" * 60)
    print("Line Junction Analysis Complete!")
    print("=" * 60)
    
    return project


def demonstrate_junction_factory():
    """Demonstrate the JunctionFactory helper methods."""
    
    print("\n" + "=" * 60)
    print("Junction Factory Demonstration")
    print("=" * 60)
    
    # Create mock structures for demonstration
    class MockSystem:
        pass
    
    wall_a = MockSystem()
    wall_b = MockSystem()
    
    # Area junction
    area_junc = JunctionFactory.create_area_junction(
        name="test_area",
        system1=wall_a,
        system2=wall_b,
        area=5.0
    )
    print(f"\nArea Junction: {area_junc.name}")
    print(f"  Type: {area_junc.junction_type}")
    print(f"  Area: {area_junc.area} m²")
    
    # Line junction (perpendicular)
    line_junc = JunctionFactory.create_perpendicular_wall_junction(
        name="corner",
        wall1=wall_a,
        wall2=wall_b,
        length=2.0
    )
    print(f"\nPerpendicular Line Junction: {line_junc.name}")
    print(f"  Type: {line_junc.junction_type}")
    print(f"  Length: {line_junc.length} m")
    print(f"  Angles: {[round(a * 180/np.pi, 1) for a in line_junc.angles]} degrees")
    
    # Line junction (parallel)
    parallel_junc = JunctionFactory.create_parallel_panel_junction(
        name="double_wall",
        panel1=wall_a,
        panel2=wall_b,
        length=3.0
    )
    print(f"\nParallel Line Junction: {parallel_junc.name}")
    print(f"  Type: {parallel_junc.junction_type}")
    print(f"  Length: {parallel_junc.length} m")
    print(f"  Angles: {[round(a * 180/np.pi, 1) for a in parallel_junc.angles]} degrees")


if __name__ == "__main__":
    # Run examples
    project = create_line_junction_example()
    
    demonstrate_junction_factory()
    
    print("\n✓ All examples completed successfully!")
