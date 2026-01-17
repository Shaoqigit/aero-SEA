"""
SEA Engine Export - Result visualization and export functionality
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import numpy as np


class ResultExporter:
    """Export simulation results to various formats."""

    EXPORTERS = {
        'csv': 'export_csv',
        'json': 'export_json',
        'png': 'export_plot',
        'pdf': 'export_pdf'
    }

    def __init__(self, results: Dict[str, Any]):
        self.results = results

    def export_csv(self, filepath: Path) -> bool:
        """Export results to CSV format."""
        try:
            import pandas as pd
            dataframes = []

            if 'energy' in self.results:
                energy = self.results['energy']
                if hasattr(energy, 'ydata') and hasattr(energy, 'xdata'):
                    df = pd.DataFrame(
                        energy.ydata,
                        columns=[f'energy_ch_{i}' for i in range(energy.ydata.shape[1])]
                    )
                    dataframes.append(df)

            if 'result' in self.results:
                result = self.results['result']
                if hasattr(result, 'ydata'):
                    df = pd.DataFrame(
                        result.ydata,
                        columns=[f'result_ch_{i}' for i in range(result.ydata.shape[1])]
                    )
                    dataframes.append(df)

            if dataframes:
                combined = pd.concat(dataframes, axis=1)
                combined.to_csv(filepath, index=False)
                return True
            return False
        except Exception as e:
            print(f"CSV export failed: {e}")
            return False

    def export_json(self, filepath: Path) -> bool:
        """Export results to JSON format."""
        import json
        try:
            export_data = {}
            for key, value in self.results.items():
                if hasattr(value, 'ydata') and hasattr(value, 'xdata'):
                    export_data[key] = {
                        'xdata': value.xdata.data.tolist() if hasattr(value.xdata, 'data') else list(value.xdata),
                        'ydata': value.ydata.tolist()
                    }
                elif isinstance(value, np.ndarray):
                    export_data[key] = value.tolist()
                else:
                    export_data[key] = str(value)

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception as e:
            print(f"JSON export failed: {e}")
            return False

    def export_plot(self, filepath: Path, **kwargs) -> bool:
        """Export results as plot image."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('SEA Analysis Results')

            # Energy plot
            if 'energy' in self.results:
                ax = axes[0, 0]
                energy = self.results['energy']
                if hasattr(energy, 'xdata') and hasattr(energy, 'ydata'):
                    freq_hz = energy.xdata.data / (2 * np.pi) if hasattr(energy.xdata, 'data') else energy.xdata / (2 * np.pi)
                    for i in range(energy.ydata.shape[1]):
                        ax.semilogy(freq_hz, energy.ydata[:, i], label=f'Channel {i+1}')
                    ax.set_xlabel('Frequency (Hz)')
                    ax.set_ylabel('Energy (J)')
                    ax.set_title('Subsystem Energy')
                    ax.legend()
                    ax.grid(True, alpha=0.3)

            # Result plot
            if 'result' in self.results:
                ax = axes[0, 1]
                result = self.results['result']
                if hasattr(result, 'xdata') and hasattr(result, 'ydata'):
                    freq_hz = result.xdata.data / (2 * np.pi) if hasattr(result.xdata, 'data') else result.xdata / (2 * np.pi)
                    for i in range(result.ydata.shape[1]):
                        ax.semilogy(freq_hz, np.abs(result.ydata[:, i]), label=f'Channel {i+1}')
                    ax.set_xlabel('Frequency (Hz)')
                    ax.set_ylabel('Response')
                    ax.set_title('System Response')
                    ax.legend()
                    ax.grid(True, alpha=0.3)

            # Power input plot
            if 'power_input' in self.results:
                ax = axes[1, 0]
                power = self.results['power_input']
                if hasattr(power, 'xdata') and hasattr(power, 'ydata'):
                    freq_hz = power.xdata.data / (2 * np.pi) if hasattr(power.xdata, 'data') else power.xdata / (2 * np.pi)
                    for i in range(power.ydata.shape[1]):
                        ax.semilogy(freq_hz, np.abs(power.ydata[:, i]), label=f'Channel {i+1}')
                    ax.set_xlabel('Frequency (Hz)')
                    ax.set_ylabel('Power (W)')
                    ax.set_title('Power Input')
                    ax.legend()
                    ax.grid(True, alpha=0.3)

            # Summary statistics
            ax = axes[1, 1]
            ax.axis('off')
            summary_text = "Summary Statistics\n\n"
            for key, value in self.results.items():
                if hasattr(value, 'ydata'):
                    max_val = np.max(np.abs(value.ydata))
                    summary_text += f"{key}: Max = {max_val:.4e}\n"
            ax.text(0.1, 0.9, summary_text, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', fontfamily='monospace')

            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return True
        except Exception as e:
            print(f"Plot export failed: {e}")
            return False

    def export_pdf(self, filepath: Path, **kwargs) -> bool:
        """Export results as PDF report."""
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            import matplotlib.pyplot as plt

            with PdfPages(filepath) as pdf:
                # Title page
                fig = plt.figure(figsize=(8.5, 11))
                fig.text(0.5, 0.5, 'SEA Analysis Report', ha='center', va='center', fontsize=24)
                fig.text(0.5, 0.4, 'Generated by SEA Engine', ha='center', va='center', fontsize=14)
                pdf.savefig(fig)
                plt.close()

                # Results plots
                for fmt in ['png']:
                    if self.export_plot(filepath.with_suffix('.png'), **kwargs):
                        img = plt.imread(filepath.with_suffix('.png'))
                        fig = plt.figure(figsize=(12, 10))
                        plt.imshow(img)
                        plt.axis('off')
                        pdf.savefig(fig)
                        plt.close()

            return True
        except Exception as e:
            print(f"PDF export failed: {e}")
            return False

    def export(self, filepath: Path, format: str = 'csv', **kwargs) -> bool:
        """Export results in specified format."""
        exporter = getattr(self, self.EXPORTERS.get(format, 'export_csv'), None)
        if exporter:
            return exporter(filepath, **kwargs)
        return False


class ResultAnalyzer:
    """Analyze and post-process simulation results."""

    @staticmethod
    def calculate_sound_pressure_level(pressure: np.ndarray, reference: float = 2e-5) -> np.ndarray:
        """Calculate SPL from sound pressure."""
        return 20 * np.log10(np.abs(pressure) / reference)

    @staticmethod
    def calculate_transmission_loss(
        pressure_source: np.ndarray,
        pressure_receiver: np.ndarray,
        area_ratio: float = 1.0
    ) -> np.ndarray:
        """Calculate transmission loss from pressure ratio."""
        tau = (pressure_receiver / pressure_source) ** 2 * area_ratio
        tau = np.clip(tau, 1e-12, None)  # Avoid log of zero
        return -10 * np.log10(tau)

    @staticmethod
    def calculate_insertion_loss(tl_before: np.ndarray, tl_after: np.ndarray) -> np.ndarray:
        """Calculate insertion loss from transmission loss values."""
        return tl_after - tl_before

    @staticmethod
    def calculate_average_spl(spectrum: np.ndarray, bands: np.ndarray) -> float:
        """Calculate average SPL over frequency bands."""
        return 10 * np.log10(np.mean(10 ** (spectrum / 10)))

    @staticmethod
    def get_octave_band_spectrum(
        narrowband: np.ndarray,
        freqs_narrow: np.ndarray,
        bands: np.ndarray
    ) -> np.ndarray:
        """Convert narrowband spectrum to octave/third-octave bands."""
        octave_spectrum = np.zeros(len(bands))
        for i, band_center in enumerate(bands):
            lower = band_center / 2 ** 0.5
            upper = band_center * 2 ** 0.5
            mask = (freqs_narrow >= lower) & (freqs_narrow < upper)
            if np.any(mask):
                octave_spectrum[i] = 10 * np.log10(
                    np.mean(10 ** (narrowband[mask] / 10))
                )
            else:
                octave_spectrum[i] = -np.inf
        return octave_spectrum
