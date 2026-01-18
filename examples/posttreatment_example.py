"""
SEA Engine Example - Post-Treatment and Result Export

This example demonstrates how to:
1. Run an SEA analysis
2. Extract all results using PostTreatment
3. Export to portable formats (JSON, HDF5)
4. Reload and visualize results
"""

import numpy as np
from pathlib import Path

# Import SEA Engine components
from sea_engine import SEAProject
from sea_engine.core.engine import (
    MaterialDefinition, StructuralElement,
    AcousticSpace, Junction, Load
)
from sea_engine.utils import PostTreatment, load_results


def create_analysis_example():
    """Run a wall-room analysis and export results."""
    
    print("=" * 60)
    print("SEA Engine - Post-Treatment Example")
    print("=" * 60)
    
    # Step 1: Create project
    project = SEAProject()
    project.metadata.name = "Wall-Room Analysis"
    project.metadata.description = "Example: Sound transmission with full result export"
    
    # Step 2: Set frequency range
    project.set_frequency_range(
        f_min=100,      # 100 Hz
        f_max=5000,     # 5 kHz
        band_type="third_octave"
    )
    
    # Step 3: Add materials
    concrete = MaterialDefinition(
        name="concrete",
        material_type="solid",
        density=1250.0,
        youngs_modulus=3.8e9,
        poisson_ratio=0.33,
        loss_factor=0.03
    )
    project.add_material(concrete)
    
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
    project.add_structure(wall)
    
    # Step 5: Add acoustic space (room)
    room = AcousticSpace(
        name="room",
        dimensions=(3.0, 4.0, 2.5),
        absorption_area=8.0,
        damping_type=["surface"]
    )
    project.add_acoustic_space(room)
    
    # Step 6: Add junction
    junction = Junction(
        name="wall_room_junction",
        junction_type="area",
        systems=(room, wall)
    )
    project.add_junction(junction)
    
    # Step 7: Add load
    power_load = Load(
        name="source_power",
        load_type="power",
        system_id=room.system_id,
        magnitude=0.001  # 1 mW
    )
    project.add_load(power_load)
    
    # Step 8: Run analysis
    print("\n[1] Running SEA analysis...")
    if not project.run_analysis():
        print("    Analysis failed!")
        return None
    
    print("    Analysis completed successfully!")
    
    return project


def demonstrate_posttreatment(project: SEAProject) -> PostTreatment:
    """Process results with PostTreatment."""
    
    print("\n[2] Processing results with PostTreatment...")
    
    # Create post-treatment processor
    pt = PostTreatment(project_name=project.metadata.name)
    
    # Set engineering units
    pt.set_units(
        energy="mJ",
        power="mW",
        velocity="mm/s"
    )
    
    # Process the model
    result_data = pt.process_model(
        model=project.engine.model,
        energy_unit="mJ",
        power_unit="mW",
        velocity_unit="mm/s"
    )
    
    # Print summary
    summary = pt.get_summary()
    print(f"    Frequency bands: {summary['frequency_bands']}")
    print(f"    Frequency range: {summary['frequency_range_hz'][0]:.0f} - {summary['frequency_range_hz'][1]:.0f} Hz")
    print(f"    Systems: {summary['num_systems']}")
    print(f"    Junctions: {summary['num_junctions']}")
    print(f"    Modal datasets: {summary['num_modal_datasets']}")
    print(f"    Units: {summary['units']}")
    
    return pt


def demonstrate_export(pt: PostTreatment, output_dir: Path) -> None:
    """Export results to portable formats."""
    
    print("\n[3] Exporting results...")
    
    # Export to JSON
    json_path = output_dir / "results.json"
    pt.export_json(json_path)
    print(f"    JSON exported: {json_path}")
    
    # Export to HDF5 (if h5py available)
    try:
        hdf5_path = output_dir / "results.h5"
        pt.export_hdf5(hdf5_path)
        print(f"    HDF5 exported: {hdf5_path}")
    except ImportError:
        print("    HDF5 export skipped (h5py not available)")
    
    # Show result structure
    print("\n[4] Result data structure:")
    print(f"    Frequency points: {len(pt.result_data.frequency_hz)}")
    print(f"    Systems: {list(pt.result_data.systems.keys())}")
    print(f"    Modal data entries: {len(pt.result_data.modal_data)}")
    for key, mdata in pt.result_data.modal_data.items():
        print(f"      - {key}: {mdata.system_type}, wave_type={mdata.wave_type}")
    
    # Show energy data
    if pt.result_data.energy:
        energy_data = np.array(pt.result_data.energy.get('data', []))
        print(f"    Energy shape: {energy_data.shape}")
        print(f"    Energy DOF IDs: {pt.result_data.energy.get('dof_id', [])}")
    
    # Show SEA matrix
    if pt.result_data.sea_matrix:
        sea_matrix = np.array(pt.result_data.sea_matrix.matrix)
        print(f"    SEA matrix shape: {sea_matrix.shape}")


def demonstrate_reload(json_path: Path) -> None:
    """Reload and verify exported results."""
    
    print("\n[5] Reloading exported results...")
    
    # Load from JSON
    loaded = load_results(json_path)
    
    print(f"    Loaded project: {loaded.project_name}")
    print(f"    Frequency bands: {len(loaded.frequency_hz)}")
    print(f"    Systems: {len(loaded.systems)}")
    print(f"    Modal datasets: {len(loaded.modal_data)}")
    
    if loaded.sea_matrix:
        print(f"    SEA matrix: {len(loaded.sea_matrix.matrix)}x{len(loaded.sea_matrix.matrix[0])}x{len(loaded.sea_matrix.matrix[0][0])}")


def demonstrate_modal_data(pt: PostTreatment) -> None:
    """Display modal density and overlap data."""
    
    print("\n[6] Modal properties:")
    
    for key, mdata in pt.result_data.modal_data.items():
        print(f"\n    {key} ({mdata.system_type}):")
        print(f"      System ID: {mdata.system_id}, Wave type: {mdata.wave_type}")
        print(f"      Modal density (first 3 bands): {mdata.modal_density[:3]}")
        print(f"      Modal overlap (first 3 bands): {mdata.modal_overlap[:3]}")


def demonstrate_units(pt: PostTreatment) -> None:
    """Show engineering unit conversions."""
    
    print("\n[7] Engineering unit conversions:")
    
    # Energy conversion
    if pt.result_data.energy:
        energy_j = np.array(pt.result_data.energy.get('data', []))
        energy_mj = energy_j * 1000  # Convert J to mJ
        print(f"    Energy: {energy_j[0,0]:.6f} J = {energy_mj[0,0]:.3f} mJ")
    
    # Power conversion  
    if pt.result_data.power_input:
        power_w = np.array(pt.result_data.power_input.get('data', []))
        power_mw = power_w * 1000  # Convert W to mW
        print(f"    Power: {power_w[0]:.6f} W = {power_mw[0]:.3f} mW")


if __name__ == "__main__":
    # Create output directory
    output_dir = Path("./examples/output/posttreatment")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis
    project = create_analysis_example()
    
    if project:
        # Process results
        pt = demonstrate_posttreatment(project)
        
        # Export results
        demonstrate_export(pt, output_dir)
        
        # Reload and verify
        demonstrate_reload(output_dir / "results.json")
        
        # Show modal data
        demonstrate_modal_data(pt)
        
        # Show units
        demonstrate_units(pt)
        
        print("\n" + "=" * 60)
        print("Post-Treatment Example Complete!")
        print("=" * 60)
        print(f"\nOutput files:")
        print(f"  - {output_dir / 'results.json'}")
        try:
            print(f"  - {output_dir / 'results.h5'}")
        except:
            pass
        print(f"\nThese files can be imported by external post-processing tools.")
