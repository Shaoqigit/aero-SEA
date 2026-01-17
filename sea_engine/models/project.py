"""
SEA Project - Project management for vibroacoustic simulations
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import json

from ..core.engine import (
    SEAEngine, MaterialDefinition, StructuralElement,
    AcousticSpace, Junction, Load, FrequencyRange
)


@dataclass
class ProjectMetadata:
    """Project metadata."""
    name: str = "Untitled Project"
    description: str = ""
    author: str = ""
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"


@dataclass
class SEAProject:
    """
    Main project class for managing vibroacoustic simulations.
    Encapsulates all model data, configurations, and results.
    """

    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    engine: SEAEngine = field(default_factory=SEAEngine)

    # Model components
    materials: Dict[str, MaterialDefinition] = field(default_factory=dict)
    structures: Dict[str, StructuralElement] = field(default_factory=dict)
    acoustic_spaces: Dict[str, AcousticSpace] = field(default_factory=dict)
    junctions: Dict[str, Junction] = field(default_factory=dict)
    loads: Dict[str, Load] = field(default_factory=dict)

    # Analysis settings
    frequency_range: FrequencyRange = field(default_factory=FrequencyRange)

    # Results storage
    results: Dict[str, Any] = field(default_factory=dict)

    # File paths
    project_file: Optional[Path] = None
    export_directory: Path = Path("./exports")

    def __post_init__(self):
        self.engine = SEAEngine()

    # Material Management
    def add_material(self, material: MaterialDefinition) -> str:
        """Add material to project."""
        self.materials[material.name] = material
        self.metadata.modified = datetime.now()
        return material.name

    def get_material(self, name: str) -> Optional[MaterialDefinition]:
        """Get material by name."""
        return self.materials.get(name)

    # Structural Element Management
    def add_structure(self, structure: StructuralElement) -> int:
        """Add structural element and return system ID."""
        self.structures[structure.name] = structure
        self.metadata.modified = datetime.now()
        return self.engine.add_structural_element(structure)

    def get_structure(self, name: str) -> Optional[StructuralElement]:
        """Get structure by name."""
        return self.structures.get(name)

    # Acoustic Space Management
    def add_acoustic_space(self, space: AcousticSpace) -> int:
        """Add acoustic space and return system ID."""
        self.acoustic_spaces[space.name] = space
        self.metadata.modified = datetime.now()
        return self.engine.add_acoustic_space(space)

    def get_acoustic_space(self, name: str) -> Optional[AcousticSpace]:
        """Get acoustic space by name."""
        return self.acoustic_spaces.get(name)

    # Junction Management
    def add_junction(self, junction: Junction, name: str = None) -> str:
        """Add junction to project."""
        junction_name = name or junction.name
        self.junctions[junction_name] = junction
        self.metadata.modified = datetime.now()
        return self.engine.add_junction(junction, junction_name)

    # Load Management
    def add_load(self, load: Load) -> str:
        """Add load to project."""
        self.loads[load.name] = load
        self.metadata.modified = datetime.now()
        return self.engine.add_load(load)

    # Analysis Methods
    def set_frequency_range(self, f_min: float, f_max: float, band_type: str = "third_octave"):
        """Set frequency range for analysis."""
        self.frequency_range = FrequencyRange(f_min, f_max, band_type)

    def build_model(self) -> bool:
        """Build SEA model from project components."""
        return self.engine.build_model()

    def solve(self) -> bool:
        """Solve the SEA model."""
        return self.engine.solve()

    def run_analysis(self) -> bool:
        """Run complete analysis workflow."""
        if not self.build_model():
            return False
        return self.solve()

    def get_results(self) -> Dict[str, Any]:
        """Get analysis results."""
        if not self.results:
            self.results = self.engine.get_energy_results()
        return self.results

    def calculate_transmission_loss(self, input_name: str, output_name: str) -> Dict[str, Any]:
        """Calculate transmission loss between two systems."""
        input_sys = self.structures.get(input_name) or self.acoustic_spaces.get(input_name)
        output_sys = self.structures.get(output_name) or self.acoustic_spaces.get(output_name)

        if input_sys and output_sys:
            input_id = getattr(input_sys, '_system_id', None)
            output_id = getattr(output_sys, '_system_id', None)
            if input_id and output_id:
                tl = self.engine.get_transmission_loss(input_id, output_id)
                return {'transmission_loss': tl, 'frequency': self.frequency_range}

        return {'error': 'Systems not found or not solved'}

    # File I/O
    def save(self, path: Path = None) -> Path:
        """Save project to JSON file."""
        if path is None and self.project_file is None:
            path = Path(f"{self.metadata.name.replace(' ', '_')}.seaproj")
        elif path is None:
            path = self.project_file

        project_data = {
            'metadata': {
                'name': self.metadata.name,
                'description': self.metadata.description,
                'author': self.metadata.author,
                'version': self.metadata.version,
                'created': self.metadata.created.isoformat(),
                'modified': self.metadata.modified.isoformat()
            },
            'frequency_range': {
                'f_min': self.frequency_range.f_min,
                'f_max': self.frequency_range.f_max,
                'band_type': self.frequency_range.band_type
            },
            'materials': {
                name: {
                    'name': mat.name,
                    'material_type': mat.material_type,
                    'density': mat.density,
                    'youngs_modulus': mat.youngs_modulus,
                    'poisson_ratio': mat.poisson_ratio,
                    'loss_factor': mat.loss_factor,
                    'porosity': mat.porosity,
                    'flow_resistivity': mat.flow_resistivity,
                    'thickness': mat.thickness
                }
                for name, mat in self.materials.items()
            },
            'structures': {
                name: {
                    'name': s.name,
                    'element_type': s.element_type,
                    'dimensions': s.dimensions,
                    'damping_loss_factor': s.damping_loss_factor,
                    'trim': s.trim
                }
                for name, s in self.structures.items()
            },
            'acoustic_spaces': {
                name: {
                    'name': s.name,
                    'volume': s.volume,
                    'surface_area': s.surface_area,
                    'dimensions': s.dimensions,
                    'absorption_area': s.absorption_area,
                    'damping_type': s.damping_type
                }
                for name, s in self.acoustic_spaces.items()
            }
        }

        with open(path, 'w') as f:
            json.dump(project_data, f, indent=2)

        self.project_file = path
        return path

    @classmethod
    def load(cls, path: Path) -> "SEAProject":
        """Load project from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        project = cls()
        project.project_file = path

        # Load metadata
        project.metadata = ProjectMetadata(
            name=data['metadata'].get('name', 'Untitled'),
            description=data['metadata'].get('description', ''),
            author=data['metadata'].get('author', ''),
            version=data['metadata'].get('version', '1.0.0'),
            created=datetime.fromisoformat(data['metadata'].get('created', datetime.now().isoformat())),
            modified=datetime.fromisoformat(data['metadata'].get('modified', datetime.now().isoformat()))
        )

        # Load frequency range
        freq = data.get('frequency_range', {})
        project.frequency_range = FrequencyRange(
            f_min=freq.get('f_min', 20.0),
            f_max=freq.get('f_max', 10000.0),
            band_type=freq.get('band_type', 'third_octave')
        )

        # Load materials
        for name, mat_data in data.get('materials', {}).items():
            project.add_material(MaterialDefinition(
                name=mat_data['name'],
                material_type=mat_data['material_type'],
                density=mat_data.get('density'),
                youngs_modulus=mat_data.get('youngs_modulus'),
                poisson_ratio=mat_data.get('poisson_ratio'),
                loss_factor=mat_data.get('loss_factor', 0.0),
                porosity=mat_data.get('porosity'),
                flow_resistivity=mat_data.get('flow_resistivity'),
                thickness=mat_data.get('thickness')
            ))

        # Load structures
        for name, struct_data in data.get('structures', {}).items():
            mat_name = struct_data.get('material')
            material = project.get_material(mat_name) if mat_name else None
            project.add_structure(StructuralElement(
                name=struct_data['name'],
                element_type=struct_data['element_type'],
                dimensions=struct_data.get('dimensions', {}),
                material=material,
                damping_loss_factor=struct_data.get('damping_loss_factor', 0.01),
                trim=struct_data.get('trim')
            ))

        # Load acoustic spaces
        for name, space_data in data.get('acoustic_spaces', {}).items():
            dims = space_data.get('dimensions')
            project.add_acoustic_space(AcousticSpace(
                name=space_data['name'],
                volume=space_data.get('volume'),
                surface_area=space_data.get('surface_area'),
                dimensions=tuple(dims) if dims else None,
                absorption_area=space_data.get('absorption_area', 0.0),
                damping_type=space_data.get('damping_type', ['surface'])
            ))

        return project
