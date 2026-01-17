"""
Configuration management for SEA Engine
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class SolverConfig:
    """Configuration for SEA solver parameters."""
    frequency_range: tuple = (20, 10000)  # Hz
    frequency_bands: str = "third_octave"  # third_octave, octave, linear
    convergence_tolerance: float = 1e-6
    max_iterations: int = 1000
    output_format: str = "engineering"  # engineering, raw


@dataclass
class GUIConfig:
    """Configuration for GUI settings."""
    theme: str = "light"
    window_size: tuple = (1280, 800)
    default_font_size: int = 10
    plot_dpi: int = 100


@dataclass
class ExportConfig:
    """Configuration for export settings."""
    export_formats: List[str] = field(default_factory=lambda: ["csv", "png", "pdf"])
    export_directory: Path = Path("./exports")
    report_template: str = "default"


@dataclass
class Config:
    """Main configuration container."""
    solver: SolverConfig = field(default_factory=SolverConfig)
    gui: GUIConfig = field(default_factory=GUIConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    pyva_path: Optional[Path] = None
    log_level: str = "INFO"

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from JSON file."""
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()

    def to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        with open(config_path, 'w') as f:
            json.dump({
                'solver': self.solver.__dict__,
                'gui': self.gui.__dict__,
                'export': self.export.__dict__,
                'pyva_path': str(self.pyva_path) if self.pyva_path else None,
                'log_level': self.log_level
            }, f, indent=2)
