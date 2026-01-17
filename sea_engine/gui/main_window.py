"""
Main GUI window for SEA Engine
"""
from typing import Optional
from pathlib import Path


class SEAMainWindow:
    """
    Main application window for SEA Engine.
    Provides user interface for vibroacoustic simulation.
    """

    def __init__(self, project=None):
        """Initialize main window."""
        self.project = project
        self.current_file: Optional[Path] = None

    def setup_ui(self):
        """Setup user interface components."""
        pass

    def show(self):
        """Display the main window."""
        pass

    def close(self):
        """Close the main window."""
        pass
