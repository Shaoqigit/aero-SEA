"""
SEA Engine Visualization - Result plotting and visualization
"""
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np


class SEAPlotter:
    """
    Comprehensive plotting class for SEA results.
    Supports energy, velocity, pressure, and transmission loss plots.
    """

    def __init__(self, results: Dict[str, Any], frequency_hz: Optional[np.ndarray] = None):
        """
        Initialize plotter with results.

        Args:
            results: Dictionary containing SEA results (energy, result, etc.)
            frequency_hz: Optional frequency array in Hz (calculated if not provided)
        """
        self.results = results
        self._freq_hz = frequency_hz

    @property
    def frequency_hz(self) -> np.ndarray:
        """Get frequency array in Hz."""
        if self._freq_hz is not None:
            return self._freq_hz

        # Try to extract from results
        for key in ['energy', 'result', 'power_input']:
            if key in self.results and hasattr(self.results[key], 'xdata'):
                xdata = self.results[key].xdata
                if hasattr(xdata, 'data'):
                    return xdata.data / (2 * np.pi)
                else:
                    return np.array(xdata) / (2 * np.pi)

        # Default frequency range
        return np.linspace(100, 5000, 17)

    def get_frequency_axis(self, xscale: str = 'log') -> np.ndarray:
        """Get frequency axis for plotting."""
        if xscale == 'log':
            return np.logspace(np.log10(self.frequency_hz[0]),
                             np.log10(self.frequency_hz[-1]),
                             100)
        return self.frequency_hz

    def plot_energy(
        self,
        ax: Any = None,
        show: bool = False,
        save_path: Optional[Path] = None,
        title: str = "Subsystem Energy",
        ylabel: str = "Energy (J)",
        **kwargs
    ) -> Any:
        """Plot energy results."""
        try:
            import matplotlib.pyplot as plt

            if ax is None:
                fig, ax = plt.subplots(figsize=(10, 6))

            if 'energy' not in self.results:
                ax.text(0.5, 0.5, "No energy data available",
                       transform=ax.transAxes, ha='center')
                return ax

            energy = self.results['energy']
            if not hasattr(energy, 'ydata'):
                ax.text(0.5, 0.5, "Invalid energy data",
                       transform=ax.transAxes, ha='center')
                return ax

            freq = self.frequency_hz
            # Get colors - use provided list or generate from colormap
            provided_colors = kwargs.get('colors')
            if provided_colors is not None and isinstance(provided_colors, (list, np.ndarray)):
                colors = provided_colors
            else:
                import matplotlib.pyplot as plt
                n_colors = energy.ydata.shape[1]
                colors = plt.cm.tab10(np.linspace(0, 1, n_colors))
            
            labels = kwargs.get('labels', [f'System {i+1}' for i in range(energy.ydata.shape[1])])

            for i in range(energy.ydata.shape[1]):
                color = colors[i] if isinstance(colors, (list, np.ndarray)) and len(colors) > i else colors
                ax.semilogy(freq, energy.ydata[:, i],
                           color=color,
                           label=labels[i],
                           linewidth=kwargs.get('linewidth', 1.5))

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3, which='both')
            ax.set_xscale(kwargs.get('xscale', 'log'))

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"Energy plot failed: {e}")
            return ax

    def plot_velocity(
        self,
        ax: Any = None,
        show: bool = False,
        save_path: Optional[Path] = None,
        title: str = "Subsystem Velocity",
        **kwargs
    ) -> Any:
        """Plot velocity results."""
        try:
            import matplotlib.pyplot as plt

            if ax is None:
                fig, ax = plt.subplots(figsize=(10, 6))

            if 'result' not in self.results:
                ax.text(0.5, 0.5, "No result data available",
                       transform=ax.transAxes, ha='center')
                return ax

            result = self.results['result']
            if not hasattr(result, 'ydata'):
                ax.text(0.5, 0.5, "Invalid result data",
                       transform=ax.transAxes, ha='center')
                return ax

            freq = self.frequency_hz
            velocity = np.abs(result.ydata)

            ax.semilogy(freq, velocity, linewidth=kwargs.get('linewidth', 1.5),
                       color=kwargs.get('color', 'steelblue'))

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Velocity (m/s)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3, which='both')
            ax.set_xscale(kwargs.get('xscale', 'log'))

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"Velocity plot failed: {e}")
            return ax

    def plot_spl(
        self,
        ax: Any = None,
        show: bool = False,
        save_path: Optional[Path] = None,
        reference: float = 2e-5,
        title: str = "Sound Pressure Level",
        **kwargs
    ) -> Any:
        """Plot sound pressure level (SPL)."""
        try:
            import matplotlib.pyplot as plt

            if ax is None:
                fig, ax = plt.subplots(figsize=(10, 6))

            if 'result' not in self.results:
                ax.text(0.5, 0.5, "No result data available",
                       transform=ax.transAxes, ha='center')
                return ax

            result = self.results['result']
            if not hasattr(result, 'ydata'):
                ax.text(0.5, 0.5, "Invalid result data",
                       transform=ax.transAxes, ha='center')
                return ax

            freq = self.frequency_hz
            pressure = np.abs(result.ydata[:, 0])  # First channel
            spl = 20 * np.log10(pressure / reference)

            ax.plot(freq, spl, linewidth=kwargs.get('linewidth', 1.5),
                   color=kwargs.get('color', 'steelblue'))
            ax.fill_between(freq, spl, alpha=0.3, color=kwargs.get('color', 'steelblue'))

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('SPL (dB re 20 μPa)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.set_xscale(kwargs.get('xscale', 'log'))

            # Add reference line
            if kwargs.get('show_reference', True):
                ref_level = kwargs.get('reference_level', 70)
                ax.axhline(y=ref_level, color='gray', linestyle='--', alpha=0.5, label=f'{ref_level} dB')

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"SPL plot failed: {e}")
            return ax

    def plot_transmission_loss(
        self,
        tl_data: np.ndarray,
        ax: Any = None,
        show: bool = False,
        save_path: Optional[Path] = None,
        title: str = "Transmission Loss",
        **kwargs
    ) -> Any:
        """Plot transmission loss."""
        try:
            import matplotlib.pyplot as plt

            if ax is None:
                fig, ax = plt.subplots(figsize=(10, 6))

            freq = self.frequency_hz

            ax.plot(freq, tl_data, linewidth=kwargs.get('linewidth', 2),
                   color=kwargs.get('color', 'darkgreen'))
            ax.fill_between(freq, tl_data, alpha=0.3, color=kwargs.get('color', 'lightgreen'))

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('TL (dB)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.set_xscale(kwargs.get('xscale', 'log'))

            # Add mass law reference
            if kwargs.get('show_mass_law', False):
                f_mass = np.logspace(np.log10(freq[0]), np.log10(freq[-1]), 100)
                # Simple mass law: TL ≈ 20log10(f*m) - 47 dB
                m = kwargs.get('mass_per_area', 10)  # kg/m²
                tl_mass = 20 * np.log10(f_mass * m) - 47
                ax.plot(f_mass, tl_mass, '--', color='gray', alpha=0.7,
                       label='Mass Law Reference', linewidth=1)
                ax.legend()

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"Transmission loss plot failed: {e}")
            return ax

    def plot_power_flow(
        self,
        ax: Any = None,
        show: bool = False,
        save_path: Optional[Path] = None,
        title: str = "Power Flow",
        **kwargs
    ) -> Any:
        """Plot power flow between subsystems."""
        try:
            import matplotlib.pyplot as plt

            if ax is None:
                fig, ax = plt.subplots(figsize=(10, 6))

            if 'power_input' not in self.results:
                ax.text(0.5, 0.5, "No power input data available",
                       transform=ax.transAxes, ha='center')
                return ax

            power = self.results['power_input']
            if not hasattr(power, 'ydata'):
                ax.text(0.5, 0.5, "Invalid power data",
                       transform=ax.transAxes, ha='center')
                return ax

            freq = self.frequency_hz
            power_data = np.abs(power.ydata)

            colors = kwargs.get('colors', plt.cm.viridis(np.linspace(0, 1, power_data.shape[1])))

            for i in range(power_data.shape[1]):
                ax.semilogy(freq, power_data[:, i],
                           color=colors[i] if isinstance(colors, list) else colors(i),
                           label=f'Path {i+1}')

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Power (W)')
            ax.set_title(title)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3, which='both')
            ax.set_xscale(kwargs.get('xscale', 'log'))

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"Power flow plot failed: {e}")
            return ax

    def create_summary_plot(
        self,
        save_path: Optional[Path] = None,
        title: str = "SEA Analysis Summary",
        **kwargs
    ) -> Any:
        """Create a comprehensive summary plot with multiple subplots."""
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle(title, fontsize=14, fontweight='bold')

            # Energy plot
            self.plot_energy(ax=axes[0, 0], **kwargs)

            # Velocity plot
            self.plot_velocity(ax=axes[0, 1], **kwargs)

            # SPL plot
            self.plot_spl(ax=axes[1, 0], **kwargs)

            # Power flow plot
            self.plot_power_flow(ax=axes[1, 1], **kwargs)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            return fig

        except Exception as e:
            print(f"Summary plot failed: {e}")
            return None

    def animate_results(
        self,
        output_path: Path,
        duration: float = 5.0,
        fps: int = 10,
        **kwargs
    ) -> bool:
        """Create animation of results over frequency (placeholder)."""
        try:
            # This is a placeholder for animation functionality
            # Full implementation would require matplotlib.animation
            print("Animation functionality - placeholder")
            print(f"Would create {duration * fps} frames at {output_path}")
            return True
        except Exception as e:
            print(f"Animation failed: {e}")
            return False


class ComparisonPlotter:
    """Plot comparison between multiple SEA models or conditions."""

    def __init__(self, plotters: List[SEAPlotter], labels: List[str]):
        """
        Initialize comparison plotter.

        Args:
            plotters: List of SEAPlotter instances
            labels: Labels for each plot
        """
        self.plotters = plotters
        self.labels = labels

    def compare_energy(
        self,
        show: bool = False,
        save_path: Optional[Path] = None,
        **kwargs
    ) -> Any:
        """Compare energy results across multiple models."""
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            colors = kwargs.get('colors', plt.cm.tab10(np.linspace(0, 1, len(self.plotters))))

            for i, (plotter, label) in enumerate(zip(self.plotters, self.labels)):
                if 'energy' in plotter.results:
                    energy = plotter.results['energy']
                    freq = plotter.frequency_hz
                    ax.semilogy(freq, energy.ydata[:, 0],
                               color=colors[i] if isinstance(colors, list) else colors(i),
                               label=label,
                               linewidth=kwargs.get('linewidth', 1.5))

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Energy (J)')
            ax.set_title(kwargs.get('title', 'Energy Comparison'))
            ax.legend()
            ax.grid(True, alpha=0.3, which='both')
            ax.set_xscale(kwargs.get('xscale', 'log'))

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"Energy comparison failed: {e}")
            return None

    def compare_transmission_loss(
        self,
        tl_data_list: List[np.ndarray],
        show: bool = False,
        save_path: Optional[Path] = None,
        **kwargs
    ) -> Any:
        """Compare transmission loss across multiple models."""
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            colors = kwargs.get('colors', plt.cm.tab10(np.linspace(0, 1, len(tl_data_list))))

            for i, (tl_data, label) in enumerate(zip(tl_data_list, self.labels)):
                freq = self.plotters[0].frequency_hz
                ax.plot(freq, tl_data,
                       color=colors[i] if isinstance(colors, list) else colors(i),
                       label=label,
                       linewidth=kwargs.get('linewidth', 2))

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Transmission Loss (dB)')
            ax.set_title(kwargs.get('title', 'Transmission Loss Comparison'))
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xscale(kwargs.get('xscale', 'log'))

            if save_path:
                plt.savefig(save_path, dpi=kwargs.get('dpi', 150), bbox_inches='tight')

            if show:
                plt.show()

            return ax

        except Exception as e:
            print(f"TL comparison failed: {e}")
            return None


def quick_plot(
    results: Dict[str, Any],
    plot_type: str = 'energy',
    save_path: Optional[Path] = None,
    **kwargs
) -> Any:
    """
    Quick plotting function for SEA results.

    Args:
        results: SEA results dictionary
        plot_type: Type of plot ('energy', 'velocity', 'spl', 'power', 'summary')
        save_path: Optional path to save figure
        **kwargs: Additional plot arguments

    Returns:
        Matplotlib axes object
    """
    plotter = SEAPlotter(results)

    plot_methods = {
        'energy': plotter.plot_energy,
        'velocity': plotter.plot_velocity,
        'spl': plotter.plot_spl,
        'power': plotter.plot_power_flow,
        'summary': plotter.create_summary_plot
    }

    plot_func = plot_methods.get(plot_type, plotter.plot_energy)
    return plot_func(save_path=save_path, **kwargs)
