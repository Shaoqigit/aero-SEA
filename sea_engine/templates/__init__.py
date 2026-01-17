"""
SEA Templates - Pre-built simulation templates for common engineering scenarios
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from ..core.engine import (
    MaterialDefinition, StructuralElement, AcousticSpace,
    Junction, Load, FrequencyRange
)


@dataclass
class BuildingAcousticTemplate:
    """Template for building acoustic analysis."""

    @staticmethod
    def create_two_rooms(
        room1_dims: tuple,
        room2_dims: tuple,
        wall_thickness: float,
        wall_material: str = "concrete"
    ) -> Dict:
        """Create two rooms separated by a wall."""
        # Material for concrete wall
        concrete = MaterialDefinition(
            name="concrete",
            material_type="solid",
            youngs_modulus=3.8e9,
            poisson_ratio=0.33,
            density=1250.0,
            loss_factor=0.03
        )

        # Wall structure
        wall = StructuralElement(
            name="wall",
            element_type="plate",
            dimensions={
                "thickness": wall_thickness,
                "Lx": room1_dims[0],
                "Ly": room1_dims[1]
            },
            material=concrete,
            damping_loss_factor=0.03
        )

        # Room 1
        room1 = AcousticSpace(
            name="room1",
            volume=room1_dims[0] * room1_dims[1] * room1_dims[2],
            surface_area=2 * (room1_dims[0]*room1_dims[1] + room1_dims[1]*room1_dims[2] + room1_dims[0]*room1_dims[2]),
            dimensions=room1_dims,
            absorption_area=8.0,
            damping_type=["surface"]
        )

        # Room 2
        room2 = AcousticSpace(
            name="room2",
            volume=room2_dims[0] * room2_dims[1] * room2_dims[2],
            surface_area=2 * (room2_dims[0]*room2_dims[1] + room2_dims[1]*room2_dims[2] + room2_dims[0]*room2_dims[2]),
            dimensions=room2_dims,
            absorption_area=10.0,
            damping_type=["surface"]
        )

        return {
            "materials": [concrete],
            "structures": [wall],
            "acoustic_spaces": [room1, room2]
        }


@dataclass
class VehicleInteriorTemplate:
    """Template for vehicle interior noise analysis."""

    @staticmethod
    def create_vehicle_cabin(
        cabin_volume: float,
        cabin_surface_area: float,
        panels: List[Dict]
    ) -> Dict:
        """Create vehicle cabin model."""
        # Cabin acoustic space
        cabin = AcousticSpace(
            name="cabin",
            volume=cabin_volume,
            surface_area=cabin_surface_area,
            absorption_area=0.0,
            damping_type=["eta", "surface"]
        )

        # Create panel structures
        structures = []
        for i, panel in enumerate(panels):
            material = MaterialDefinition(
                name=panel.get("material_name", f"panel_material_{i}"),
                material_type="solid",
                youngs_modulus=panel.get("E", 210e9),
                poisson_ratio=panel.get("nu", 0.3),
                density=panel.get("rho", 7800.0),
                loss_factor=panel.get("eta", 0.01)
            )

            structure = StructuralElement(
                name=panel.get("name", f"panel_{i}"),
                element_type="plate",
                dimensions={
                    "thickness": panel.get("thickness", 0.001),
                    "Lx": panel.get("Lx", 1.0),
                    "Ly": panel.get("Ly", 1.0)
                },
                material=material,
                damping_loss_factor=panel.get("eta", 0.01)
            )
            structures.append(structure)

        return {
            "materials": [s.material for s in structures if s.material],
            "structures": structures,
            "acoustic_spaces": [cabin]
        }


@dataclass
class EquipmentEnclosureTemplate:
    """Template for equipment enclosure analysis."""

    @staticmethod
    def create_box_enclosure(
        dimensions: tuple,
        plate_thickness: float,
        material_name: str = "steel",
        with_treatment: bool = False
    ) -> Dict:
        """Create box enclosure model."""
        # Material
        steel = MaterialDefinition(
            name=material_name,
            material_type="solid",
            youngs_modulus=210e9,
            poisson_ratio=0.3,
            density=7800.0,
            loss_factor=0.0
        )

        # Plate property
        plate_prop = StructuralElement(
            name=f"{material_name}_plate",
            element_type="plate",
            dimensions={
                "thickness": plate_thickness,
                "Lx": dimensions[0],
                "Ly": dimensions[1]
            },
            material=steel,
            damping_loss_factor=0.01
        )

        # Internal volume
        volume = dimensions[0] * dimensions[1] * dimensions[2]
        surface_area = 2 * (dimensions[0]*dimensions[1] + dimensions[1]*dimensions[2] + dimensions[0]*dimensions[2])
        perimeter = 4 * (dimensions[0] + dimensions[1] + dimensions[2])

        enclosure = AcousticSpace(
            name="enclosure_cavity",
            volume=volume,
            surface_area=surface_area,
            perimeter=perimeter,
            absorption_area=0.0,
            damping_type=["surface"]
        )

        return {
            "materials": [steel],
            "structures": [plate_prop],
            "acoustic_spaces": [enclosure]
        }


class TemplateLibrary:
    """Library of pre-built simulation templates."""

    TEMPLATES = {
        "building_acoustic_two_rooms": BuildingAcousticTemplate.create_two_rooms,
        "vehicle_cabin": VehicleInteriorTemplate.create_vehicle_cabin,
        "equipment_enclosure": EquipmentEnclosureTemplate.create_box_enclosure
    }

    @classmethod
    def list_templates(cls) -> List[str]:
        """List available templates."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template(cls, name: str):
        """Get template by name."""
        return cls.TEMPLATES.get(name)
