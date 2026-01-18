"""
SEA Templates - Pre-built simulation templates for common engineering scenarios
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from ..core.engine import (
    MaterialDefinition, StructuralElement, AcousticSpace,
    Junction, Load, FrequencyRange
)


@dataclass
class BuildingAcousticTemplate:
    """Template for building acoustic analysis."""

    @staticmethod
    def create_wall_room(
        room_dims: Tuple[float, float, float],
        wall_thickness: float,
        wall_dims: Tuple[float, float],
        material_name: str = "concrete",
        damping: float = 0.03,
        absorption_area: float = 8.0
    ) -> Dict:
        """
        Create a simple wall-room model (room with one wall).

        Args:
            room_dims: Room dimensions (Lx, Ly, Lz) in meters
            wall_thickness: Wall thickness in meters
            wall_dims: Wall dimensions (width, height) in meters
            material_name: Wall material type
            damping: Damping loss factor
            absorption_area: Room absorption area in m²

        Returns:
            Dictionary with materials, structures, and acoustic spaces
        """
        # Material
        material_props = {
            "concrete": {"E": 3.8e9, "nu": 0.33, "rho": 1250.0, "eta": 0.03},
            "brick": {"E": 2.0e9, "nu": 0.25, "rho": 1800.0, "eta": 0.02},
            "glass": {"E": 70e9, "nu": 0.23, "rho": 2500.0, "eta": 0.001},
            "gypsum": {"E": 2.0e9, "nu": 0.30, "rho": 800.0, "eta": 0.02},
        }
        props = material_props.get(material_name, material_props["concrete"])

        material = MaterialDefinition(
            name=material_name,
            material_type="solid",
            youngs_modulus=props["E"],
            poisson_ratio=props["nu"],
            density=props["rho"],
            loss_factor=props["eta"]
        )

        # Wall
        wall = StructuralElement(
            name="wall",
            element_type="plate",
            dimensions={
                "thickness": wall_thickness,
                "Lx": wall_dims[0],
                "Ly": wall_dims[1]
            },
            material=material,
            damping_loss_factor=damping
        )

        # Room
        room = AcousticSpace(
            name="room",
            dimensions=room_dims,
            absorption_area=absorption_area,
            damping_type=["surface"]
        )

        return {
            "materials": [material],
            "structures": [wall],
            "acoustic_spaces": [room]
        }

    @staticmethod
    def create_double_wall(
        room1_dims: Tuple[float, float, float],
        room2_dims: Tuple[float, float, float],
        wall1_thickness: float,
        wall2_thickness: float,
        cavity_width: float,
        wall_material: str = "concrete",
        damping: float = 0.03
    ) -> Dict:
        """
        Create double wall model (two walls with cavity between rooms).

        Args:
            room1_dims: First room dimensions (Lx, Ly, Lz)
            room2_dims: Second room dimensions (Lx, Ly, Lz)
            wall1_thickness: First wall thickness in meters
            wall2_thickness: Second wall thickness in meters
            cavity_width: Cavity width between walls
            wall_material: Wall material type
            damping: Damping loss factor

        Returns:
            Dictionary with materials, structures, and acoustic spaces
        """
        material_props = {
            "concrete": {"E": 3.8e9, "nu": 0.33, "rho": 1250.0, "eta": 0.03},
            "brick": {"E": 2.0e9, "nu": 0.25, "rho": 1800.0, "eta": 0.02},
            "glass": {"E": 70e9, "nu": 0.23, "rho": 2500.0, "eta": 0.001},
            "gypsum": {"E": 2.0e9, "nu": 0.30, "rho": 800.0, "eta": 0.02},
        }
        props = material_props.get(wall_material, material_props["concrete"])

        material = MaterialDefinition(
            name=wall_material,
            material_type="solid",
            youngs_modulus=props["E"],
            poisson_ratio=props["nu"],
            density=props["rho"],
            loss_factor=props["eta"]
        )

        # Wall 1
        wall1 = StructuralElement(
            name="wall1",
            element_type="plate",
            dimensions={
                "thickness": wall1_thickness,
                "Lx": room1_dims[0],
                "Ly": room1_dims[1]
            },
            material=material,
            damping_loss_factor=damping
        )

        # Wall 2
        wall2 = StructuralElement(
            name="wall2",
            element_type="plate",
            dimensions={
                "thickness": wall2_thickness,
                "Lx": room2_dims[0],
                "Ly": room2_dims[1]
            },
            material=material,
            damping_loss_factor=damping
        )

        # Room 1 (source)
        room1 = AcousticSpace(
            name="room1",
            dimensions=room1_dims,
            absorption_area=8.0,
            damping_type=["surface"]
        )

        # Room 2 (receiver)
        room2 = AcousticSpace(
            name="room2",
            dimensions=room2_dims,
            absorption_area=10.0,
            damping_type=["surface"]
        )

        return {
            "materials": [material],
            "structures": [wall1, wall2],
            "acoustic_spaces": [room1, room2]
        }


@dataclass
class VehicleInteriorTemplate:
    """Template for vehicle interior noise analysis."""

    @staticmethod
    def create_vehicle_cabin(
        cabin_volume: float,
        cabin_surface_area: float,
        panels: List[Dict],
        damping_type: List[str] = None
    ) -> Dict:
        """
        Create vehicle cabin model with multiple panels.

        Args:
            cabin_volume: Cabin interior volume in m³
            cabin_surface_area: Total interior surface area in m²
            panels: List of panel specifications with keys:
                - name: Panel name
                - area: Panel area in m²
                - thickness: Panel thickness in m
                - material: Material type (steel, aluminum, etc.)
                - E: Young's modulus (optional)
                - nu: Poisson ratio (optional)
                - rho: Density (optional)
                - eta: Damping loss factor (optional)
            damping_type: Damping type list

        Returns:
            Dictionary with materials, structures, and acoustic spaces
        """
        material_defaults = {
            "steel": {"E": 210e9, "nu": 0.3, "rho": 7800.0, "eta": 0.001},
            "aluminum": {"E": 70e9, "nu": 0.33, "rho": 2700.0, "eta": 0.001},
            "plastic": {"E": 2.5e9, "nu": 0.35, "rho": 1200.0, "eta": 0.02},
            "composite": {"E": 50e9, "nu": 0.28, "rho": 1600.0, "eta": 0.005},
            "glass": {"E": 70e9, "nu": 0.23, "rho": 2500.0, "eta": 0.001},
        }

        cabin = AcousticSpace(
            name="cabin",
            volume=cabin_volume,
            surface_area=cabin_surface_area,
            absorption_area=0.0,
            damping_type=list(damping_type) if damping_type else ["eta", "surface"]
        )

        structures = []
        materials = []

        for i, panel in enumerate(panels):
            mat_type = panel.get("material", "steel")
            defaults = material_defaults.get(mat_type, material_defaults["steel"])

            material = MaterialDefinition(
                name=f"{mat_type}_{i}",
                material_type="solid",
                youngs_modulus=panel.get("E", defaults["E"]),
                poisson_ratio=panel.get("nu", defaults["nu"]),
                density=panel.get("rho", defaults["rho"]),
                loss_factor=panel.get("eta", defaults["eta"])
            )
            materials.append(material)

            # Calculate dimensions from area
            area = panel.get("area", 1.0)
            thickness = panel.get("thickness", 0.001)
            Lx = panel.get("Lx", max(0.3, min(2.0, area ** 0.5)))
            Ly = panel.get("Ly", area / Lx) if Lx > 0 else 1.0

            structure = StructuralElement(
                name=panel.get("name", f"panel_{i}"),
                element_type="plate",
                dimensions={
                    "thickness": thickness,
                    "Lx": Lx,
                    "Ly": Ly
                },
                material=material,
                damping_loss_factor=panel.get("eta", defaults["eta"])
            )
            structures.append(structure)

        return {
            "materials": materials,
            "structures": structures,
            "acoustic_spaces": [cabin]
        }

    @staticmethod
    def create_car_model() -> Dict:
        """Create a typical passenger car interior model."""

        # Cabin parameters
        cabin_volume = 3.0  # m³ (small car)
        cabin_surface_area = 18.0  # m²

        # Typical car panels
        panels = [
            {"name": "floor", "area": 2.5, "thickness": 0.0008, "material": "steel", "eta": 0.005},
            {"name": "roof", "area": 2.0, "thickness": 0.0007, "material": "steel", "eta": 0.005},
            {"name": "firewall", "area": 1.5, "thickness": 0.0008, "material": "steel", "eta": 0.005},
            {"name": "door_panel_left", "area": 1.2, "thickness": 0.0006, "material": "plastic", "eta": 0.02},
            {"name": "door_panel_right", "area": 1.2, "thickness": 0.0006, "material": "plastic", "eta": 0.02},
            {"name": "rear_shelf", "area": 1.0, "thickness": 0.001, "material": "plastic", "eta": 0.02},
            {"name": "front_windshield", "area": 1.8, "thickness": 0.004, "material": "glass", "eta": 0.001},
            {"name": "rear_window", "area": 1.2, "thickness": 0.004, "material": "glass", "eta": 0.001},
        ]

        return VehicleInteriorTemplate.create_vehicle_cabin(
            cabin_volume=cabin_volume,
            cabin_surface_area=cabin_surface_area,
            panels=panels
        )


@dataclass
class EquipmentEnclosureTemplate:
    """Template for equipment enclosure analysis."""

    @staticmethod
    def create_box_enclosure(
        dimensions: Tuple[float, float, float],
        plate_thickness: float,
        material_name: str = "steel",
        damping: float = 0.01
    ) -> Dict:
        """
        Create a simple box enclosure.

        Args:
            dimensions: Enclosure dimensions (Lx, Ly, Lz) in meters
            plate_thickness: Wall thickness in meters
            material_name: Plate material type
            damping: Damping loss factor

        Returns:
            Dictionary with materials, structures, and acoustic spaces
        """
        material_props = {
            "steel": {"E": 210e9, "nu": 0.3, "rho": 7800.0},
            "aluminum": {"E": 70e9, "nu": 0.33, "rho": 2700.0},
            "plastic": {"E": 2.5e9, "nu": 0.35, "rho": 1200.0},
        }
        props = material_props.get(material_name, material_props["steel"])

        material = MaterialDefinition(
            name=material_name,
            material_type="solid",
            youngs_modulus=props["E"],
            poisson_ratio=props["nu"],
            density=props["rho"],
            loss_factor=damping
        )

        # Create plates for each face
        structures = []
        Lx, Ly, Lz = dimensions

        plate_configs = [
            ("plate_x1", Lz, Ly),  # x=0 face
            ("plate_x2", Lz, Ly),  # x=1 face
            ("plate_y1", Lx, Lz),  # y=0 face
            ("plate_y2", Lx, Lz),  # y=1 face
            ("plate_z1", Lx, Ly),  # z=0 face (floor)
            ("plate_z2", Lx, Ly),  # z=1 face (top)
        ]

        for name, dim1, dim2 in plate_configs:
            plate = StructuralElement(
                name=name,
                element_type="plate",
                dimensions={
                    "thickness": plate_thickness,
                    "Lx": dim1,
                    "Ly": dim2
                },
                material=material,
                damping_loss_factor=damping
            )
            structures.append(plate)

        # Internal cavity
        volume = Lx * Ly * Lz
        surface_area = 2 * (Lx*Ly + Ly*Lz + Lx*Lz)

        enclosure = AcousticSpace(
            name="enclosure_cavity",
            volume=volume,
            surface_area=surface_area,
            absorption_area=0.0,
            damping_type=["surface"]
        )

        return {
            "materials": [material],
            "structures": structures,
            "acoustic_spaces": [enclosure]
        }

    @staticmethod
    def create_treated_enclosure(
        dimensions: Tuple[float, float, float],
        plate_thickness: float,
        treatment_thickness: float = 0.05,
        treatment_material: str = "fiberglass",
        plate_material: str = "steel"
    ) -> Dict:
        """
        Create an enclosure with acoustic treatment.

        Args:
            dimensions: Enclosure dimensions (Lx, Ly, Lz) in meters
            plate_thickness: Wall thickness in meters
            treatment_thickness: Sound absorption thickness in meters
            treatment_material: Treatment material type
            plate_material: Plate material type

        Returns:
            Dictionary with materials, structures, and acoustic spaces
        """
        # Base enclosure
        base = EquipmentEnclosureTemplate.create_box_enclosure(
            dimensions=dimensions,
            plate_thickness=plate_thickness,
            material_name=plate_material,
            damping=0.01
        )

        # Add treatment material
        treatment = MaterialDefinition(
            name=treatment_material,
            material_type="equivalent_fluid",
            density=10.0,
            flow_resistivity=25000.0,
            porosity=0.98,
            tortuosity=1.02
        )

        return {
            "materials": base["materials"] + [treatment],
            "structures": base["structures"],
            "acoustic_spaces": base["acoustic_spaces"]
        }


@dataclass
class IndustrialNoiseTemplate:
    """Template for industrial noise control analysis."""

    @staticmethod
    def create_machine_enclosure(
        machine_dims: Tuple[float, float, float],
        enclosure_gap: float = 0.1,
        enclosure_thickness: float = 0.001,
        material: str = "steel"
    ) -> Dict:
        """
        Create an enclosure around a noise source.

        Args:
            machine_dims: Machine dimensions (Lx, Ly, Lz) in meters
            enclosure_gap: Gap between machine and enclosure in meters
            enclosure_thickness: Enclosure wall thickness in meters
            material: Enclosure material type

        Returns:
            Dictionary with materials, structures, and acoustic spaces
        """
        # Enclosure dimensions
        Lx = machine_dims[0] + 2 * enclosure_gap
        Ly = machine_dims[1] + 2 * enclosure_gap
        Lz = machine_dims[2] + 2 * enclosure_gap

        return EquipmentEnclosureTemplate.create_box_enclosure(
            dimensions=(Lx, Ly, Lz),
            plate_thickness=enclosure_thickness,
            material_name=material
        )

    @staticmethod
    def create_barrier_model(
        source_dims: Tuple[float, float],
        barrier_height: float,
        barrier_width: float,
        barrier_distance: float,
        receiver_distance: float
    ) -> Dict:
        """
        Create a simple barrier model (infinite line source).

        Args:
            source_dims: Source dimensions (width, height) in meters
            barrier_height: Barrier height in meters
            barrier_width: Barrier width in meters
            barrier_distance: Distance from source to barrier in meters
            receiver_distance: Distance from barrier to receiver in meters

        Returns:
            Dictionary with structures and acoustic spaces
        """
        # Create barrier as a plate
        barrier = StructuralElement(
            name="barrier",
            element_type="plate",
            dimensions={
                "thickness": 0.01,  # 1 cm thick barrier
                "Lx": barrier_width,
                "Ly": barrier_height
            },
            material=MaterialDefinition(
                name="barrier_material",
                material_type="solid",
                youngs_modulus=25e9,
                poisson_ratio=0.2,
                density=2300.0,
                loss_factor=0.02
            ),
            damping_loss_factor=0.02
        )

        # Source region (point of noise generation)
        source = AcousticSpace(
            name="source_zone",
            volume=source_dims[0] * source_dims[1] * 0.5,
            surface_area=2 * (source_dims[0] * source_dims[1]),
            absorption_area=0.0,
            damping_type=["surface"]
        )

        # Receiver region
        receiver = AcousticSpace(
            name="receiver_zone",
            volume=2.0 * 3.0 * 2.5,
            surface_area=2 * (2.0*3.0 + 3.0*2.5 + 2.0*2.5),
            absorption_area=5.0,
            damping_type=["surface"]
        )

        return {
            "materials": [barrier.material],
            "structures": [barrier],
            "acoustic_spaces": [source, receiver]
        }


class JunctionFactory:
    """Factory for creating SEA junctions with common configurations."""

    @staticmethod
    def create_area_junction(
        name: str,
        system1: Any,
        system2: Any,
        area: float = None
    ) -> 'Junction':
        """
        Create an area junction between two systems.

        Args:
            name: Junction name
            system1: First system (structural or acoustic)
            system2: Second system (structural or acoustic)
            area: Coupling area in m² (auto-calculated if not provided)

        Returns:
            Junction object
        """
        return Junction(
            name=name,
            junction_type="area",
            systems=(system1, system2),
            area=area
        )

    @staticmethod
    def create_line_junction(
        name: str,
        system1: Any,
        system2: Any,
        length: float = 1.0,
        angle_degrees: float = 90.0
    ) -> 'Junction':
        """
        Create a line junction for edge couplings (beam-plate connections).

        Line junctions represent edge-to-edge couplings where two plates
        meet at an angle (typically 90 degrees for perpendicular walls).

        Args:
            name: Junction name
            system1: First plate/structure
            system2: Second plate/structure
            length: Coupling length in meters (default: 1.0m)
            angle_degrees: Angle between systems in degrees (default: 90°)

        Returns:
            Junction object
        """
        angle_rad = angle_degrees * np.pi / 180.0
        return Junction(
            name=name,
            junction_type="line",
            systems=(system1, system2),
            length=length,
            angles=(0, angle_rad)
        )

    @staticmethod
    def create_perpendicular_wall_junction(
        name: str,
        wall1: Any,
        wall2: Any,
        length: float = 1.0
    ) -> 'Junction':
        """
        Create a junction for two perpendicular walls (90 degrees).

        Common for corner connections in buildings where walls meet at right angles.

        Args:
            name: Junction name
            wall1: First wall structure
            wall2: Second wall structure
            length: Junction length in meters

        Returns:
            Junction object
        """
        return JunctionFactory.create_line_junction(
            name=name,
            system1=wall1,
            system2=wall2,
            length=length,
            angle_degrees=90.0
        )

    @staticmethod
    def create_parallel_panel_junction(
        name: str,
        panel1: Any,
        panel2: Any,
        length: float = 1.0
    ) -> 'Junction':
        """
        Create a junction for two parallel panels (0 degrees).

        Used for double-wall configurations where panels are parallel.

        Args:
            name: Junction name
            panel1: First panel structure
            panel2: Second panel structure
            length: Junction length in meters

        Returns:
            Junction object
        """
        return JunctionFactory.create_line_junction(
            name=name,
            system1=panel1,
            system2=panel2,
            length=length,
            angle_degrees=0.0
        )


class TemplateLibrary:
    """Library of pre-built simulation templates."""

    TEMPLATES = {
        # Building acoustics
        "wall_room": BuildingAcousticTemplate.create_wall_room,
        "double_wall": BuildingAcousticTemplate.create_double_wall,

        # Vehicle interiors
        "vehicle_cabin": VehicleInteriorTemplate.create_vehicle_cabin,
        "car_model": VehicleInteriorTemplate.create_car_model,

        # Equipment enclosures
        "box_enclosure": EquipmentEnclosureTemplate.create_box_enclosure,
        "treated_enclosure": EquipmentEnclosureTemplate.create_treated_enclosure,

        # Industrial noise
        "machine_enclosure": IndustrialNoiseTemplate.create_machine_enclosure,
        "barrier": IndustrialNoiseTemplate.create_barrier_model,
    }

    @classmethod
    def list_templates(cls) -> List[str]:
        """List available templates."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template(cls, name: str) -> Optional[Any]:
        """Get template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def get_template_info(cls, name: str) -> Dict:
        """Get template information."""
        template = cls.get_template(name)
        if template:
            doc = template.__doc__ or ""
            return {
                "name": name,
                "description": doc.split("\n")[0] if doc else "",
                "function": template
            }
        return {}

    @classmethod
    def print_template_list(cls) -> None:
        """Print all available templates."""
        print("Available SEA Templates:")
        print("-" * 50)
        for name in sorted(cls.TEMPLATES.keys()):
            info = cls.get_template_info(name)
            print(f"  {name:25s} - {info['description']}")
