"""
SEA Post-Treatment Module - Comprehensive result export for post-processing

This module provides:
- Modal density extraction
- Modal overlap calculation  
- SEA matrix extraction
- Engineering unit conversions
- Portable HDF5/JSON export for external tools
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Engineering unit conversion factors
UNIT_CONVERSIONS = {
    # Energy
    "J_to_mJ": 1000.0,
    "J_to_uJ": 1e6,
    
    # Power
    "W_to_mW": 1000.0,
    "W_to_uW": 1e6,
    
    # Pressure/SPL
    "Pa_to_uPa": 1e6,
    
    # Velocity
    "m/s_to_mm/s": 1000.0,
    "m/s_to_um/s": 1e6,
    
    # Length
    "m_to_mm": 1000.0,
    "m_to_um": 1e6,
    
    # Area
    "m2_to_cm2": 10000.0,
    "m2_to_mm2": 1e6,
}


@dataclass
class ModalData:
    """Modal properties for a single SEA system."""
    system_id: int
    system_name: str
    system_type: str  # "plate", "beam", "cavity", "room"
    wave_type: int  # DOF type (3=bending, 5=longitudinal, 0=acoustic)
    modal_density: List[float]  # modes/Hz
    modal_overlap: List[float]  # dimensionless
    frequency: List[float]  # Hz
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class JunctionData:
    """Coupling junction data."""
    junction_name: str
    junction_type: str  # "area", "line", "semi_infinite"
    system1_id: int
    system2_id: int
    area: Optional[float] = None  # m²
    length: Optional[float] = None  # m
    angles: Optional[List[float]] = None  # radians
    coupling_loss_factor: Optional[List[List[float]]] = None  # CLF matrix per frequency
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SEAMatrixData:
    """SEA matrix data."""
    matrix: List[List[List[float]]]  # Real part only for JSON
    frequency: List[float]  # Hz
    system_ids: List[int]
    system_types: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "matrix": [[[float(x.real) for x in row] for row in freq] for freq in self.matrix],
            "frequency": [float(x) for x in self.frequency],
            "system_ids": [int(x) for x in self.system_ids],
            "system_types": [str(x) for x in self.system_types]
        }


@dataclass
class ResultData:
    """Complete result data structure for export."""
    # Metadata
    project_name: str
    analysis_type: str = "SEA"
    export_format: str = "1.0"
    
    # Frequency
    frequency_hz: List[float] = field(default_factory=list)
    frequency_rad: List[float] = field(default_factory=list)
    
    # Systems
    systems: Dict[str, Dict] = field(default_factory=dict)
    
    # Modal data per system
    modal_data: Dict[str, ModalData] = field(default_factory=dict)
    
    # Junctions
    junctions: Dict[str, JunctionData] = field(default_factory=dict)
    
    # Energy results (Signal format)
    energy: Dict[str, Any] = field(default_factory=dict)
    
    # General results (Signal format)  
    result: Dict[str, Any] = field(default_factory=dict)
    
    # Power inputs
    power_input: Dict[str, Any] = field(default_factory=dict)
    
    # SEA Matrix
    sea_matrix: Optional[SEAMatrixData] = None
    
    # Load cases
    loads: Dict[str, Dict] = field(default_factory=dict)
    
    # Engineering units used
    units: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export."""
        result = {
            "metadata": {
                "project_name": self.project_name,
                "analysis_type": self.analysis_type,
                "export_format": self.export_format,
                "units": self.units
            },
            "frequency": {
                "hz": [float(x) for x in self.frequency_hz],
                "rad_s": [float(x) for x in self.frequency_rad]
            },
            "systems": self.systems,
            "modal_data": {k: v.to_dict() for k, v in self.modal_data.items()},
            "junctions": {k: v.to_dict() for k, v in self.junctions.items()},
            "loads": self.loads
        }
        
        # Add energy if present
        if self.energy:
            result["energy"] = {
                "data": [[float(x) for x in row] for row in self.energy.get("data", [])],
                "dof_id": [int(x) for x in self.energy.get("dof_id", [])],
                "dof_type": [int(x) for x in self.energy.get("dof_type", [])]
            }
        
        # Add result if present
        if self.result:
            result["result"] = {
                "data": [[float(x) for x in row] for row in self.result.get("data", [])],
                "dof_id": [int(x) for x in self.result.get("dof_id", [])],
                "dof_type": [int(x) for x in self.result.get("dof_type", [])]
            }
        
        # Add power_input if present
        if self.power_input:
            result["power_input"] = {
                "data": [float(x) for x in self.power_input.get("data", [])],
                "dof_id": [int(x) for x in self.power_input.get("dof_id", [])]
            }
        
        # Add SEA matrix if present
        if self.sea_matrix:
            result["sea_matrix"] = self.sea_matrix.to_dict()
        
        return result


class PostTreatment:
    """
    Post-treatment class for SEA results.
    
    Extracts and processes all results from a solved Pyva model,
    converts to engineering units, and exports to portable formats.
    """
    
    def __init__(self, project_name: str = "SEA_Analysis"):
        self.project_name = project_name
        self.result_data = ResultData(project_name=project_name)
        self._units = {
            "energy": "J",
            "power": "W",
            "velocity": "m/s",
            "pressure": "Pa",
            "length": "m",
            "area": "m²"
        }
    
    def set_units(self, **units: str) -> None:
        """Set engineering units for output."""
        valid_units = {
            "energy": ["J", "mJ", "uJ"],
            "power": ["W", "mW", "uW"],
            "velocity": ["m/s", "mm/s", "um/s"],
            "pressure": ["Pa", "uPa"],
            "length": ["m", "mm", "um"],
            "area": ["m²", "cm²", "mm²"]
        }
        
        for key, value in units.items():
            if key in valid_units and value in valid_units[key]:
                self._units[key] = value
            else:
                logger.warning(f"Ignoring invalid unit: {key}={value}")
    
    def process_model(
        self,
        model: Any,
        energy_unit: str = "mJ",
        power_unit: str = "mW",
        velocity_unit: str = "mm/s"
    ) -> ResultData:
        """
        Process a solved Pyva model and extract all results.
        
        Args:
            model: Solved Pyva HybridModel
            energy_unit: Output energy unit (J, mJ, uJ)
            power_unit: Output power unit (W, mW, uW)
            velocity_unit: Output velocity unit (m/s, mm/s, um/s)
            
        Returns:
            ResultData object with all extracted results
        """
        self._units["energy"] = energy_unit
        self._units["power"] = power_unit
        self._units["velocity"] = velocity_unit
        
        # Extract frequency
        self._extract_frequency(model)
        
        # Extract system information
        self._extract_systems(model)
        
        # Extract modal data
        self._extract_modal_data(model)
        
        # Extract junction data
        self._extract_junctions(model)
        
        # Extract energy results
        self._extract_energy(model)
        
        # Extract general results
        self._extract_result(model)
        
        # Extract power input
        self._extract_power_input(model)
        
        # Extract SEA matrix
        self._extract_sea_matrix(model)
        
        # Extract load cases
        self._extract_loads(model)
        
        return self.result_data
    
    def _extract_frequency(self, model: Any) -> None:
        """Extract frequency data."""
        try:
            xdata = model.xdata
            if hasattr(xdata, 'data'):
                freq_rad = np.array(xdata.data).flatten()
                self.result_data.frequency_rad = freq_rad.tolist()
                # Convert to Hz
                self.result_data.frequency_hz = (freq_rad / (2 * np.pi)).tolist()
            else:
                # Fallback
                self.result_data.frequency_rad = xdata.flatten().tolist()
                self.result_data.frequency_hz = (np.array(xdata.flatten()) / (2 * np.pi)).tolist()
        except Exception as e:
            logger.warning(f"Could not extract frequency data: {e}")
    
    def _extract_systems(self, model: Any) -> None:
        """Extract system information."""
        try:
            systems = model.systems
            for sys_id, sys in systems.items():
                sys_info = {
                    "id": sys_id,
                    "type": type(sys).__name__,
                }
                
                # Add dimensions if available
                if hasattr(sys, 'Lx'):
                    sys_info["Lx"] = sys.Lx
                if hasattr(sys, 'Ly'):
                    sys_info["Ly"] = sys.Ly
                if hasattr(sys, 'Lz'):
                    sys_info["Lz"] = sys.Lz
                if hasattr(sys, 'volume'):
                    sys_info["volume"] = sys.volume
                if hasattr(sys, 'area'):
                    sys_info["area"] = sys.area
                    
                # Add material info if available
                if hasattr(sys, 'prop') and hasattr(sys.prop, 'material'):
                    mat = sys.prop.material
                    sys_info["material"] = {
                        "type": type(mat).__name__,
                        "density": mat.rho0 if hasattr(mat, 'rho0') else None,
                        "youngs_modulus": mat.E if hasattr(mat, 'E') else None,
                    }
                
                self.result_data.systems[str(sys_id)] = sys_info
        except Exception as e:
            logger.warning(f"Could not extract system data: {e}")
    
    def _extract_modal_data(self, model: Any) -> None:
        """Extract modal density and overlap for each system."""
        try:
            freq_rad = np.array(self.result_data.frequency_rad)
            freq_hz = np.array(self.result_data.frequency_hz)
            
            systems = model.systems
            for sys_id, sys in systems.items():
                # Get wave DOF info
                try:
                    wave_dof = sys.wave_DOF(sys_id)
                    wave_types = wave_dof.DOF
                except:
                    wave_types = [3]  # Default to bending for plates
                
                # For each wave type, compute modal properties
                for wave_type in wave_types:
                    try:
                        # Modal density
                        if hasattr(sys, 'modal_density'):
                            modal_density = sys.modal_density(freq_rad, wave_DOF=wave_type)
                            modal_density = np.array(modal_density).flatten()
                            
                            # Modal overlap
                            if hasattr(sys, 'modal_overlap'):
                                modal_overlap = sys.modal_overlap(freq_rad, wave_DOF=wave_type)
                                modal_overlap = np.array(modal_overlap).flatten()
                            else:
                                modal_overlap = modal_density * 0  # Placeholder
                            
                            # Create modal data object
                            key = f"sys{sys_id}_wave{wave_type}"
                            self.result_data.modal_data[key] = ModalData(
                                system_id=sys_id,
                                system_name=type(sys).__name__,
                                system_type=self._get_system_type(sys),
                                wave_type=wave_type,
                                modal_density=modal_density.tolist(),
                                modal_overlap=modal_overlap.tolist(),
                                frequency=freq_hz.tolist()
                            )
                    except Exception as e:
                        logger.debug(f"Could not extract modal data for system {sys_id}: {e}")
                        
        except Exception as e:
            logger.warning(f"Could not extract modal data: {e}")
    
    def _get_system_type(self, sys: Any) -> str:
        """Determine system type string."""
        sys_type = type(sys).__name__
        if "Plate" in sys_type:
            return "plate"
        elif "Beam" in sys_type:
            return "beam"
        elif "Room" in sys_type or "Cavity" in sys_type:
            return "cavity"
        else:
            return "structural"
    
    def _extract_junctions(self, model: Any) -> None:
        """Extract junction information."""
        try:
            junctions = model.junctions
            for jname, junc in junctions.items():
                jdata = JunctionData(
                    junction_name=jname,
                    junction_type=type(junc).__name__,
                    system1_id=0,
                    system2_id=0
                )
                
                # Get coupled systems
                if hasattr(junc, 'systems'):
                    systems = junc.systems
                    if len(systems) >= 2:
                        jdata.system1_id = systems[0].ID if hasattr(systems[0], 'ID') else 0
                        jdata.system2_id = systems[1].ID if hasattr(systems[1], 'ID') else 0
                
                # Get area/length
                if hasattr(junc, 'area'):
                    jdata.area = float(junc.area) if junc.area else None
                if hasattr(junc, 'length'):
                    jdata.length = float(junc.length) if junc.length else None
                if hasattr(junc, 'thetas'):
                    jdata.angles = [float(t) for t in junc.thetas] if junc.thetas else None
                
                # Coupling loss factor
                if hasattr(junc, 'coupling_loss_factor'):
                    clf = np.array(junc.coupling_loss_factor)
                    jdata.coupling_loss_factor = clf.real.tolist()
                
                self.result_data.junctions[jname] = jdata
                
        except Exception as e:
            logger.warning(f"Could not extract junction data: {e}")
    
    def _extract_energy(self, model: Any) -> None:
        """Extract energy results."""
        try:
            if hasattr(model, 'energy'):
                energy = model.energy
                data = np.array(energy.ydata)
                
                # Convert to requested units
                data = self._convert_energy(data)
                
                # Extract DOF info
                dof = energy.dof
                dof_id = dof.ID.tolist() if hasattr(dof, 'ID') else []
                dof_type = dof.DOF.tolist() if hasattr(dof, 'DOF') else []
                
                self.result_data.energy = {
                    "data": data.tolist(),
                    "dof_id": dof_id,
                    "dof_type": dof_type
                }
        except Exception as e:
            logger.warning(f"Could not extract energy data: {e}")
    
    def _extract_result(self, model: Any) -> None:
        """Extract general results."""
        try:
            if hasattr(model, 'result'):
                result = model.result
                data = np.array(result.ydata)
                
                # Convert to requested units based on DOF type
                data = self._convert_result_data(data, result.dof)
                
                dof = result.dof
                dof_id = dof.ID.tolist() if hasattr(dof, 'ID') else []
                dof_type = dof.DOF.tolist() if hasattr(dof, 'DOF') else []
                
                self.result_data.result = {
                    "data": data.tolist(),
                    "dof_id": dof_id,
                    "dof_type": dof_type
                }
        except Exception as e:
            logger.warning(f"Could not extract result data: {e}")
    
    def _extract_power_input(self, model: Any) -> None:
        """Extract power input data."""
        try:
            if hasattr(model, 'power_input'):
                power = model.power_input
                data = np.array(power.ydata)
                
                # Convert power units
                data = self._convert_power(data)
                
                dof = power.dof
                dof_id = dof.ID.tolist() if hasattr(dof, 'ID') else []
                
                self.result_data.power_input = {
                    "data": data.tolist(),
                    "dof_id": dof_id
                }
        except Exception as e:
            logger.warning(f"Could not extract power input data: {e}")
    
    def _extract_sea_matrix(self, model: Any) -> None:
        """Extract SEA matrix."""
        try:
            if hasattr(model, 'SEAmatrix'):
                sea_matrix = model.SEAmatrix
                data = np.array(sea_matrix.data)
                
                # Get system IDs and types
                system_ids = list(model.systems.keys())
                system_types = [type(s).__name__ for s in model.systems.values()]
                
                self.result_data.sea_matrix = SEAMatrixData(
                    matrix=data.real.tolist(),  # Store real part (imaginary should be near zero)
                    frequency=self.result_data.frequency_hz,
                    system_ids=system_ids,
                    system_types=system_types
                )
        except Exception as e:
            logger.warning(f"Could not extract SEA matrix: {e}")
    
    def _extract_loads(self, model: Any) -> None:
        """Extract load case information."""
        try:
            loads = model.loads
            for lname, load in loads.items():
                load_info = {
                    "name": lname,
                    "type": str(load.DOF) if hasattr(load, 'DOF') else "unknown"
                }
                if hasattr(load, 'spectrum'):
                    load_info["spectrum"] = load.spectrum.tolist()
                self.result_data.loads[lname] = load_info
        except Exception as e:
            logger.warning(f"Could not extract load data: {e}")
    
    def _convert_energy(self, data: np.ndarray) -> np.ndarray:
        """Convert energy to requested units."""
        unit = self._units.get("energy", "J")
        if unit == "mJ":
            return data * 1000.0
        elif unit == "uJ":
            return data * 1e6
        return data
    
    def _convert_power(self, data: np.ndarray) -> np.ndarray:
        """Convert power to requested units."""
        unit = self._units.get("power", "W")
        if unit == "mW":
            return data * 1000.0
        elif unit == "uW":
            return data * 1e6
        return data
    
    def _convert_result_data(self, data: np.ndarray, dof: Any) -> np.ndarray:
        """Convert result data based on DOF type."""
        try:
            dof_types = dof.DOF if hasattr(dof, 'DOF') else []
            for i, dtype in enumerate(dof_types):
                # DOF 0 = acoustic pressure
                # DOF 3 = bending energy
                # DOF 5 = longitudinal energy
                # DOF 7 = velocity
                if dtype == 0:  # Pressure
                    pass  # Keep as Pa
                elif dtype == 7:  # Velocity
                    unit = self._units.get("velocity", "m/s")
                    if unit == "mm/s":
                        data[:, i] *= 1000.0
                    elif unit == "um/s":
                        data[:, i] *= 1e6
            return data
        except:
            return data
    
    def export_json(self, filepath: Union[str, Path]) -> None:
        """
        Export results to JSON file.
        
        Args:
            filepath: Output file path
        """
        import json
        
        filepath = Path(filepath)
        
        # Convert result data to dict with proper type conversion
        def convert_to_serializable(obj):
            """Recursively convert numpy types to Python native types."""
            if isinstance(obj, np.ndarray):
                return [convert_to_serializable(x) for x in obj.tolist()]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, complex):
                return {"real": float(obj.real), "imag": float(obj.imag)}
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(x) for x in obj]
            else:
                return obj
        
        # Convert result data to dict
        data = self.result_data.to_dict()
        data = convert_to_serializable(data)
        
        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results exported to {filepath}")
    
    def export_hdf5(self, filepath: Union[str, Path]) -> None:
        """
        Export results to HDF5 file for large datasets.
        
        Requires h5py package. Falls back to JSON if not available.
        
        Args:
            filepath: Output file path
        """
        try:
            import h5py
            
            filepath = Path(filepath)
            
            with h5py.File(filepath, 'w') as f:
                # Metadata
                meta = f.create_group('metadata')
                meta.attrs['project_name'] = self.result_data.project_name
                meta.attrs['analysis_type'] = self.result_data.analysis_type
                meta.attrs['export_format'] = self.result_data.export_format
                
                # Units
                units = f.create_group('units')
                for key, value in self._units.items():
                    units.attrs[key] = value
                
                # Frequency
                freq = f.create_group('frequency')
                freq.create_dataset('hz', data=np.array(self.result_data.frequency_hz))
                freq.create_dataset('rad_s', data=np.array(self.result_data.frequency_rad))
                
                # Systems
                systems = f.create_group('systems')
                for sys_id, sys_info in self.result_data.systems.items():
                    sys_grp = systems.create_group(sys_id)
                    for key, value in sys_info.items():
                        if isinstance(value, (int, float, str)):
                            sys_grp.attrs[key] = value
                
                # Modal data
                modal = f.create_group('modal_data')
                for key, mdata in self.result_data.modal_data.items():
                    mgrp = modal.create_group(key)
                    mgrp.create_dataset('modal_density', data=np.array(mdata.modal_density))
                    mgrp.create_dataset('modal_overlap', data=np.array(mdata.modal_overlap))
                    mgrp.create_dataset('frequency', data=np.array(mdata.frequency))
                    mgrp.attrs['system_id'] = mdata.system_id
                    mgrp.attrs['wave_type'] = mdata.wave_type
                
                # Energy
                if self.result_data.energy:
                    energy = f.create_group('energy')
                    energy.create_dataset('data', data=np.array(self.result_data.energy.get('data', [])))
                    energy.create_dataset('dof_id', data=np.array(self.result_data.energy.get('dof_id', [])))
                    energy.create_dataset('dof_type', data=np.array(self.result_data.energy.get('dof_type', [])))
                
                # SEA Matrix
                if self.result_data.sea_matrix:
                    sea = f.create_group('sea_matrix')
                    sea.create_dataset('matrix', data=np.array(self.result_data.sea_matrix.matrix))
                    sea.create_dataset('frequency', data=np.array(self.result_data.sea_matrix.frequency))
                    sea.create_dataset('system_ids', data=np.array(self.result_data.sea_matrix.system_ids))
                
            logger.info(f"Results exported to HDF5 file: {filepath}")
            
        except ImportError:
            logger.warning("h5py not available, falling back to JSON export")
            json_path = str(filepath).replace('.h5', '.json').replace('.hdf5', '.json')
            self.export_json(json_path)
    
    def get_summary(self) -> Dict:
        """Get a summary of extracted results."""
        return {
            "project": self.project_name,
            "frequency_bands": len(self.result_data.frequency_hz),
            "frequency_range_hz": [
                min(self.result_data.frequency_hz) if self.result_data.frequency_hz else None,
                max(self.result_data.frequency_hz) if self.result_data.frequency_hz else None
            ],
            "num_systems": len(self.result_data.systems),
            "num_junctions": len(self.result_data.junctions),
            "num_modal_datasets": len(self.result_data.modal_data),
            "has_energy": bool(self.result_data.energy),
            "has_sea_matrix": self.result_data.sea_matrix is not None,
            "units": self._units
        }


def load_results(filepath: Union[str, Path]) -> ResultData:
    """
    Load results from exported file.
    
    Args:
        filepath: Path to JSON or HDF5 file
        
    Returns:
        ResultData object
    """
    filepath = Path(filepath)
    
    if filepath.suffix == '.h5' or filepath.suffix == '.hdf5':
        return _load_hdf5(filepath)
    else:
        return _load_json(filepath)


def _load_json(filepath: Path) -> ResultData:
    """Load results from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    result = ResultData(project_name=data.get('metadata', {}).get('project_name', 'Loaded'))
    
    # Load frequency
    result.frequency_hz = data.get('frequency', {}).get('hz', [])
    result.frequency_rad = data.get('frequency', {}).get('rad_s', [])
    
    # Load systems
    result.systems = data.get('systems', {})
    
    # Load modal data
    for key, mdata in data.get('modal_data', {}).items():
        result.modal_data[key] = ModalData(**mdata)
    
    # Load junctions
    for key, jdata in data.get('junctions', {}).items():
        result.junctions[key] = JunctionData(**jdata)
    
    # Load energy
    result.energy = data.get('energy', {})
    
    # Load result
    result.result = data.get('result', {})
    
    # Load SEA matrix
    if data.get('sea_matrix'):
        result.sea_matrix = SEAMatrixData(**data['sea_matrix'])
    
    return result


def _load_hdf5(filepath: Path) -> ResultData:
    """Load results from HDF5 file."""
    import h5py
    
    result = ResultData(project_name="Loaded from HDF5")
    
    with h5py.File(filepath, 'r') as f:
        # Load metadata
        result.project_name = f['metadata'].attrs.get('project_name', 'Loaded')
        
        # Load frequency
        result.frequency_hz = f['frequency']['hz'][:].tolist()
        result.frequency_rad = f['frequency']['rad_s'][:].tolist()
        
        # Load systems
        for sys_id in f['systems']:
            sys_grp = f['systems'][sys_id]
            result.systems[sys_id] = {k: v for k, v in sys_grp.attrs.items()}
        
        # Load modal data
        for key in f['modal_data']:
            mgrp = f['modal_data'][key]
            result.modal_data[key] = ModalData(
                system_id=mgrp.attrs['system_id'],
                system_name=mgrp.attrs.get('system_name', ''),
                system_type=mgrp.attrs.get('system_type', ''),
                wave_type=mgrp.attrs['wave_type'],
                modal_density=mgrp['modal_density'][:].tolist(),
                modal_overlap=mgrp['modal_overlap'][:].tolist(),
                frequency=mgrp['frequency'][:].tolist()
            )
        
        # Load energy
        if 'energy' in f:
            energy = f['energy']
            result.energy = {
                'data': energy['data'][:].tolist(),
                'dof_id': energy['dof_id'][:].tolist(),
                'dof_type': energy['dof_type'][:].tolist()
            }
        
        # Load SEA matrix
        if 'sea_matrix' in f:
            sea = f['sea_matrix']
            result.sea_matrix = SEAMatrixData(
                matrix=sea['matrix'][:].tolist(),
                frequency=sea['frequency'][:].tolist(),
                system_ids=sea['system_ids'][:].tolist(),
                system_types=[s.decode() if isinstance(s, bytes) else s for s in sea['system_ids'][:]]
            )
    
    return result
