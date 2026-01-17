"""
SEA Engine - Main computation engine wrapper for Pyva
Vibroacoustic simulation software for engineering applications.
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrequencyRange:
    """Frequency range specification for SEA analysis."""
    f_min: float = 20.0
    f_max: float = 10000.0
    band_type: str = "third_octave"
    num_points: int = 100

    def to_angular_frequency(self) -> Any:
        """Convert to angular frequency array."""
        try:
            import pyva.data.matrixClasses as mC
            if self.band_type == "third_octave":
                result = mC.DataAxis.octave_band(f_max=self.f_max * 2 * np.pi)
                return result
            else:
                return np.linspace(self.f_min, self.f_max, self.num_points) * 2 * np.pi
        except Exception as e:
            logger.warning(f"Pyva not available, using fallback: {e}")
            return np.logspace(np.log10(self.f_min), np.log10(self.f_max), self.num_points) * 2 * np.pi


@dataclass
class MaterialDefinition:
    """Material definition for SEA systems."""
    name: str
    material_type: str
    density: Optional[float] = None
    speed_of_sound: Optional[float] = None
    bulk_modulus: Optional[float] = None
    loss_factor: float = 0.0
    youngs_modulus: Optional[float] = None
    poisson_ratio: Optional[float] = None
    porosity: Optional[float] = None
    flow_resistivity: Optional[float] = None
    tortuosity: Optional[float] = None
    thickness: Optional[float] = None

    def to_pyva_material(self) -> Any:
        """Convert to Pyva material object."""
        try:
            import pyva.properties.materialClasses as matC
            if self.material_type == "fluid":
                return matC.Fluid(
                    rho0=self.density if self.density else 1.208,
                    c0=self.speed_of_sound if self.speed_of_sound else 343.0,
                    eta=self.loss_factor
                )
            elif self.material_type == "solid":
                return matC.IsoMat(
                    E=self.youngs_modulus if self.youngs_modulus else 210e9,
                    nu=self.poisson_ratio if self.poisson_ratio else 0.3,
                    rho0=self.density if self.density else 7800.0,
                    eta=self.loss_factor
                )
            elif self.material_type == "equivalent_fluid":
                return matC.EquivalentFluid(
                    porosity=self.porosity if self.porosity else 0.98,
                    flow_res=self.flow_resistivity if self.flow_resistivity else 25000.0,
                    tortuosity=self.tortuosity if self.tortuosity else 1.02,
                    rho0=self.density if self.density else 1.208
                )
        except Exception as e:
            logger.error(f"Failed to create Pyva material: {e}")
            return None


@dataclass
class StructuralElement:
    """Structural element definition for SEA systems."""
    name: str
    element_type: str
    dimensions: Dict[str, float] = field(default_factory=dict)
    material: Optional[MaterialDefinition] = None
    damping_loss_factor: float = 0.01
    trim: Optional[Dict] = None
    system_id: Optional[int] = None

    def to_pyva_property(self) -> Any:
        """Convert to Pyva structural property."""
        try:
            import pyva.properties.structuralPropertyClasses as stPC
            if self.element_type == "plate" and self.material:
                mat_obj = self.material.to_pyva_material()
                if mat_obj:
                    thickness = self.dimensions.get("thickness", 0.01)
                    return stPC.PlateProp(thickness, mat_obj)
        except Exception as e:
            logger.error(f"Failed to create Pyva property: {e}")
        return None


@dataclass
class AcousticSpace:
    """Acoustic cavity definition for SEA systems."""
    name: str
    volume: Optional[float] = None
    surface_area: Optional[float] = None
    perimeter: Optional[float] = None
    dimensions: Optional[Tuple[float, float, float]] = None
    absorption_area: float = 0.0
    damping_type: List[str] = field(default_factory=lambda: ["surface"])
    system_id: Optional[int] = None

    def to_pyva_system(self, sys_id: int, fluid: Any) -> Any:
        """Convert to Pyva acoustic system."""
        try:
            import pyva.systems.acoustic3Dsystems as ac3Dsys
            if self.dimensions:
                return ac3Dsys.RectangularRoom(
                    sys_id,
                    self.dimensions[0],
                    self.dimensions[1],
                    self.dimensions[2],
                    fluid,
                    absorption_area=self.absorption_area,
                    damping_type=self.damping_type
                )
            else:
                return ac3Dsys.Acoustic3DSystem(
                    sys_id,
                    self.volume if self.volume else 1.0,
                    self.surface_area if self.surface_area else 1.0,
                    self.perimeter if self.perimeter else 1.0,
                    fluid,
                    absorption_area=self.absorption_area,
                    damping_type=self.damping_type
                )
        except Exception as e:
            logger.error(f"Failed to create Pyva system: {e}")
            return None


@dataclass
class Junction:
    """Coupling junction between SEA systems."""
    name: str
    junction_type: str
    systems: Tuple[Any, ...]
    area: Optional[float] = None
    length: Optional[float] = None
    angles: Optional[Tuple[float, ...]] = None
    fluid: Optional[Any] = None

    def to_pyva_junction(self) -> Any:
        """Convert to Pyva junction object."""
        try:
            import pyva.coupling.junctions as con
            if self.junction_type == "area":
                area_val = int(self.area) if self.area else None
                return con.AreaJunction(self.systems, area=area_val)
            elif self.junction_type == "line":
                angles = self.angles if self.angles else (0, 90*np.pi/180, 180*np.pi/180)
                return con.LineJunction(
                    self.systems,
                    length=self.length if self.length else 1.0,
                    thetas=angles
                )
            elif self.junction_type == "semi_infinite":
                return con.SemiInfiniteFluid(self.systems, self.fluid)
        except Exception as e:
            logger.error(f"Failed to create Pyva junction: {e}")
        return None


@dataclass
class Load:
    """Load definition for SEA analysis."""
    name: str
    load_type: str
    system_id: int
    wave_dof: int = 0
    magnitude: float = 1.0
    spectrum: Optional[np.ndarray] = None

    def to_pyva_load(self, frequency_axis: Any) -> Any:
        """Convert to Pyva load object."""
        try:
            import pyva.loads.loadCase as lC
            import pyva.data.dof as dof
            dof_type = dof.DOFtype(typestr=self.load_type)
            dof_obj = dof.DOF(self.system_id, self.wave_dof, dof_type)
            if self.spectrum is None:
                spectrum = self.magnitude * np.ones(frequency_axis.shape)
            else:
                spectrum = self.spectrum
            return lC.Load(frequency_axis, spectrum, dof_obj, name=self.name)
        except Exception as e:
            logger.error(f"Failed to create Pyva load: {e}")
        return None


class SEAEngine:
    """Main SEA Engine class that wraps Pyva functionality for engineering applications."""

    def __init__(self, config=None):
        self.config = config
        self.systems: List[Any] = []
        self.junctions: Dict[str, Junction] = {}
        self.loads: Dict[str, Load] = {}
        self.model: Any = None
        self.results: Any = None
        self._system_counter = 0
        self._pyva_available = self._check_pyva()

    def _check_pyva(self) -> bool:
        """Check if Pyva is available."""
        try:
            import pyva
            # Check if it's the correct pyva (vibroacoustic) by looking for specific modules
            import pyva.models
            import pyva.properties.materialClasses
            return True
        except (ImportError, AttributeError):
            logger.warning("Pyva vibroacoustic library not installed.")
            return False

    def create_frequency_axis(self) -> Any:
        """Create frequency axis for analysis."""
        if self.config:
            freq_config = FrequencyRange(
                f_min=self.config.solver.frequency_range[0],
                f_max=self.config.solver.frequency_range[1],
                band_type=self.config.solver.frequency_bands
            )
            return freq_config.to_angular_frequency()
        return FrequencyRange().to_angular_frequency()

    def add_structural_element(self, element: StructuralElement) -> int:
        """Add structural element and return system ID."""
        self._system_counter += 1
        element.system_id = self._system_counter
        self.systems.append(element)
        return self._system_counter

    def add_acoustic_space(self, space: AcousticSpace) -> int:
        """Add acoustic space and return system ID."""
        self._system_counter += 1
        space.system_id = self._system_counter
        self.systems.append(space)
        return self._system_counter

    def add_junction(self, junction: Junction, name: Optional[str] = None) -> str:
        """Add coupling junction."""
        junction_name = name if name else junction.name
        self.junctions[junction_name] = junction
        return junction_name

    def add_load(self, load: Load) -> str:
        """Add load case."""
        self.loads[load.name] = load
        return load.name

    def build_model(self) -> bool:
        """Build Pyva HybridModel from defined components."""
        if not self._pyva_available:
            logger.error("Cannot build model: Pyva not available")
            return False

        try:
            import pyva.models as mds
            import pyva.properties.materialClasses as matC
            import pyva.systems.structure2Dsystems as st2Dsys
            import pyva.coupling.junctions as con

            omega = self.create_frequency_axis()
            pyva_systems = []
            system_map = {}  # Maps wrapper objects to Pyva objects

            # Create default fluid
            air = matC.Fluid()

            for system in self.systems:
                pyva_sys = None
                if isinstance(system, StructuralElement):
                    prop = system.to_pyva_property()
                    if prop and system.system_id:
                        if system.element_type == "plate":
                            pyva_sys = st2Dsys.RectangularPlate(
                                system.system_id,
                                system.dimensions.get("Lx", 1.0),
                                system.dimensions.get("Ly", 1.0),
                                prop=prop
                            )
                elif isinstance(system, AcousticSpace) and system.system_id:
                    pyva_sys = system.to_pyva_system(system.system_id, air)

                if pyva_sys:
                    pyva_systems.append(pyva_sys)
                    system_map[id(system)] = pyva_sys

            if not pyva_systems:
                logger.warning("No systems to build model from")
                return False

            # Add flat_cavity_sw attribute to cavity systems (Pyva bug workaround)
            for pyva_sys in pyva_systems:
                if hasattr(pyva_sys, 'iscavity') and pyva_sys.iscavity():
                    if not hasattr(pyva_sys, 'flat_cavity_sw'):
                        pyva_sys.flat_cavity_sw = False

            # Create hybrid model
            self.model = mds.HybridModel(tuple(pyva_systems), xdata=omega)

            # Add junctions - use Pyva system objects
            for jname, junction in self.junctions.items():
                # Convert wrapper systems to Pyva systems
                pyva_sys_objects = []
                for s in junction.systems:
                    if id(s) in system_map:
                        pyva_sys_objects.append(system_map[id(s)])
                    else:
                        pyva_sys_objects.append(s)
                
                # Create junction - handle 2-system case only (Pyva limitation)
                if len(pyva_sys_objects) == 2:
                    pyva_junction = con.AreaJunction(
                        tuple(pyva_sys_objects),
                        area=int(junction.area) if junction.area else None
                    )
                    self.model.add_junction({jname: pyva_junction})
                elif len(pyva_sys_objects) > 2:
                    # For 3+ systems, create separate junctions for each pair
                    logger.warning(f"Junction {jname} has {len(pyva_sys_objects)} systems. "
                                 f"Pyva supports 2-system junctions. Creating pair-wise junctions.")
                    for i in range(len(pyva_sys_objects) - 1):
                        pair_junction = con.AreaJunction(
                            (pyva_sys_objects[i], pyva_sys_objects[i+1]),
                            area=int(junction.area) if junction.area else None
                        )
                        self.model.add_junction({f"{jname}_{i}": pair_junction})

            # Add loads
            for lname, load in self.loads.items():
                pyva_load = load.to_pyva_load(omega)
                if pyva_load:
                    self.model.add_load(lname, pyva_load)

            return True

        except Exception as e:
            logger.error(f"Failed to build model: {e}")
            return False

    def solve(self) -> bool:
        """Solve the SEA model."""
        if not self.model:
            if not self.build_model():
                return False

        try:
            self.model.create_SEA_matrix()
            self.model.solve()
            return True
        except Exception as e:
            logger.error(f"Solution failed: {e}")
            return False

    def get_energy_results(self) -> Dict[str, Any]:
        """Get energy results from solved model."""
        if self.model and hasattr(self.model, 'energy'):
            result = {
                'energy': self.model.energy,
                'result': self.model.result
            }
            if hasattr(self.model, 'power_input'):
                result['power_input'] = self.model.power_input
            return result
        return {}

    def get_transmission_loss(self, input_system: int, output_system: int) -> np.ndarray:
        """Calculate transmission loss between two systems."""
        return np.zeros(10)
