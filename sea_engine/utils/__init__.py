"""
SEA Engine Utilities - Helper functions for vibroacoustic analysis
"""
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class FrequencyConverter:
    """Utility class for frequency conversions."""

    @staticmethod
    def hz_to_angular(freq_hz: np.ndarray) -> np.ndarray:
        """Convert frequency from Hz to rad/s."""
        return 2 * np.pi * freq_hz

    @staticmethod
    def angular_to_hz(freq_rad: np.ndarray) -> np.ndarray:
        """Convert frequency from rad/s to Hz."""
        return freq_rad / (2 * np.pi)

    @staticmethod
    def get_third_octave_bands(f_min: float, f_max: float) -> np.ndarray:
        """Get third octave band center frequencies."""
        # Reference frequency for third octave bands
        f_ref = 1000.0
        # Number of bands
        n_min = int(np.round(10 * np.log10(f_min / f_ref)))
        n_max = int(np.round(10 * np.log10(f_max / f_ref)))
        bands = np.arange(n_min, n_max + 1)
        # Center frequencies
        freq_hz = f_ref * 10 ** (bands / 10)
        return freq_hz


class ResultFormatter:
    """Utility class for formatting simulation results."""

    @staticmethod
    def format_spl(sound_pressure: np.ndarray, reference: float = 2e-5) -> np.ndarray:
        """Calculate sound pressure level from pressure."""
        return 20 * np.log10(sound_pressure / reference)

    @staticmethod
    def format_tl(transmission_loss: np.ndarray) -> np.ndarray:
        """Format transmission loss values."""
        return transmission_loss

    @staticmethod
    def format_energy(energy: np.ndarray) -> np.ndarray:
        """Format energy values."""
        return energy

    @staticmethod
    def calculate_insertion_loss(
        tl_before: np.ndarray,
        tl_after: np.ndarray
    ) -> np.ndarray:
        """Calculate insertion loss from transmission loss values."""
        return tl_after - tl_before


class UnitConverter:
    """Utility class for unit conversions."""

    # Pressure
    PA_TO_PASCAL = 1.0
    PA_TO_MPA = 1e-6
    PA_TO_KPA = 1e-3

    # Length
    M_TO_MM = 1000.0
    M_TO_CM = 100.0
    MM_TO_M = 0.001

    # Mass
    KG_TO_G = 1000.0
    KG_TO_TONNE = 0.001

    # Frequency
    HZ_TO_KHZ = 0.001
    KHZ_TO_HZ = 1000.0

    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str) -> float:
        """Convert between units."""
        conversion_factors = {
            ("Pa", "Pa"): 1.0,
            ("Pa", "MPa"): 1e-6,
            ("m", "mm"): 1000.0,
            ("mm", "m"): 0.001,
            ("kg", "g"): 1000.0,
            ("Hz", "kHz"): 0.001,
        }
        key = (from_unit, to_unit)
        return value * conversion_factors.get(key, 1.0)


class MaterialLibrary:
    """Pre-defined material library for common engineering materials."""

    MATERIALS = {
        "steel": {
            "name": "Steel",
            "density": 7800.0,  # kg/m³
            "youngs_modulus": 210e9,  # Pa
            "poisson_ratio": 0.3,
            "loss_factor": 0.0001,
            "speed_of_sound": 5100.0  # m/s
        },
        "aluminum": {
            "name": "Aluminum",
            "density": 2700.0,
            "youngs_modulus": 70e9,
            "poisson_ratio": 0.33,
            "loss_factor": 0.0001,
            "speed_of_sound": 5100.0
        },
        "concrete": {
            "name": "Concrete",
            "density": 2400.0,
            "youngs_modulus": 30e9,
            "poisson_ratio": 0.2,
            "loss_factor": 0.03,
            "speed_of_sound": 3200.0
        },
        "glass": {
            "name": "Glass",
            "density": 2500.0,
            "youngs_modulus": 70e9,
            "poisson_ratio": 0.23,
            "loss_factor": 0.001,
            "speed_of_sound": 5200.0
        },
        "plywood": {
            "name": "Plywood",
            "density": 600.0,
            "youngs_modulus": 6e9,
            "poisson_ratio": 0.3,
            "loss_factor": 0.02,
            "speed_of_sound": 3000.0
        },
        "air": {
            "name": "Air",
            "density": 1.208,  # kg/m³
            "speed_of_sound": 343.0,  # m/s
            "bulk_modulus": 142000.0,  # Pa
            "loss_factor": 0.0
        },
        "fiberglass": {
            "name": "Fiberglass",
            "density": 10.0,  # kg/m³ (bulk)
            "flow_resistivity": 25000.0,  # Pa·s/m²
            "porosity": 0.98,
            "tortuosity": 1.02
        }
    }

    @classmethod
    def get_material(cls, name: str) -> Optional[Dict]:
        """Get material properties by name."""
        return cls.MATERIALS.get(name.lower())

    @classmethod
    def list_materials(cls) -> List[str]:
        """List available materials."""
        return list(cls.MATERIALS.keys())


class FileManager:
    """Utility class for file operations."""

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Ensure directory exists, create if necessary."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_file_extension(path: Path) -> str:
        """Get file extension without dot."""
        return path.suffix[1:] if path.suffix else ""

    @staticmethod
    def validate_extension(path: Path, allowed: List[str]) -> bool:
        """Check if file has allowed extension."""
        return FileManager.get_file_extension(path) in allowed
