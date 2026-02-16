import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
from .calculations import (
    calculate_pf,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_zt,
    DEFAULT_LORENZ,
)


def process_sample_data(df, lorenz=DEFAULT_LORENZ):
    """
    Processes a single sample's DataFrame to calculate derived properties.
    Expected columns: 'Temperature' (K), 'Seebeck' (V/K), 'Sigma' (S/m), 'Kappa_total' (W/mK).
    """
    # Make a copy to avoid modifying the original
    df = df.copy()

    # Ensure numeric and drop rows with missing critical data
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Temperature", "Seebeck", "Sigma", "Kappa_total"])

    if df.empty:
        raise ValueError("No valid data rows after cleaning")

    # PF
    df["Power Factor"] = calculate_pf(df["Seebeck"], df["Sigma"])
    df["PF_mW"] = df["Power Factor"] * 1000.0

    # Display columns for plotting alignment
    df["Sigma_Scm"] = df["Sigma"] * 0.01
    df["S_uVK"] = df["Seebeck"] * 1e6

    # Kappa_e
    df["Electronic TC"] = calculate_kappa_e(df["Sigma"], df["Temperature"], lorenz)

    # Lattice TC
    df["Lattice TC"] = calculate_kappa_l(df["Kappa_total"], df["Electronic TC"])

    # ZT
    df["ZT"] = calculate_zt(df["Power Factor"], df["Temperature"], df["Kappa_total"])

    return df


def run_multi_sample_analysis(sample_dict, export_path=None):
    """
    Processes multiple samples and generates comparison plots.

    Args:
        sample_dict (dict): {SampleName: Path/DataFrame}
        export_path (str): Optional path to save the multi-sheet Excel file.
    """
    processed_samples = {}

    for name, source in sample_dict.items():
        if isinstance(source, str):
            if source.endswith(".csv"):
                df = pd.read_csv(source)
            elif source.endswith(".xlsx"):
                # If it's a single path to an Excel, we'll assume we iterate through sheets later?
                # Actually, the dict approach implies one source per sample name.
                df = pd.read_excel(source)
            else:
                continue
        else:
            df = source

        processed_df = process_sample_data(df)
        processed_samples[name] = processed_df

    # Plotting
    plot_comparisons(processed_samples)

    # Export
    if export_path:
        with pd.ExcelWriter(export_path) as writer:
            for name, df in processed_samples.items():
                df.to_excel(writer, sheet_name=name, index=False)

    return processed_samples


def plot_comparisons(processed_samples, settings=None, show=True):
    """
    Generates overlaid plots for all samples with optional custom settings.
    Returns a list of figures if show=False.
    """
    if not settings:
        properties = [
            ("Sigma_Scm", "Electrical Conductivity (S/cm)"),
            ("S_uVK", "Seebeck Coefficient (μV/K)"),
            ("PF_mW", "Power Factor (mW/mK²)"),
            ("Kappa_total", "Total Thermal Cond. (W/mK)"),
            ("Electronic TC", "Electronic TC (W/mK)"),
            ("Lattice TC", "Lattice TC (W/mK)"),
            ("ZT", "ZT"),
        ]
        multi_panel = False
        sample_styles = None
    else:
        properties = settings.get("selected_props", [])
        multi_panel = settings.get("multi_panel", False)
        sample_styles = settings.get("sample_styles", None)

    if not properties:
        return []

    style_context = ["science", "notebook", "no-latex"]
    figs = []

    with plt.style.context(style_context):
        if multi_panel:
            n_plots = len(properties)
            rows = settings.get("rows", 1)
            cols = settings.get("cols", 2)

            if n_plots > rows * cols:
                cols = (n_plots + rows - 1) // rows

            fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 5))
            if n_plots == 1:
                axes = [axes]
            else:
                axes = axes.flatten()

            for i, (prop, ylabel) in enumerate(properties):
                ax = axes[i]
                has_data = False
                for name, df in processed_samples.items():
                    if prop in df.columns and not df[prop].isna().all():
                        style = sample_styles.get(name) if sample_styles else None
                        label = style["label"] if style else name
                        color = style["color"] if style else None
                        marker = style["marker"] if style else "o"

                        ax.plot(
                            df["Temperature"],
                            df[prop],
                            marker=marker,
                            label=label,
                            color=color,
                            markersize=4,
                        )
                        has_data = True

                ax.set_xlabel("Temperature (K)")
                ax.set_ylabel(ylabel)
                ax.set_title(f"{prop} vs. T")
                ax.grid(True)
                if has_data:
                    ax.legend()

            for j in range(i + 1, len(axes)):
                axes[j].axis("off")

            plt.tight_layout()
            figs.append(fig)
            if show:
                plt.show()
        else:
            for prop, ylabel in properties:
                fig = plt.figure(figsize=(8, 6))
                has_data = False
                for name, df in processed_samples.items():
                    if prop in df.columns and not df[prop].isna().all():
                        style = sample_styles.get(name) if sample_styles else None
                        label = style["label"] if style else name
                        color = style["color"] if style else None
                        marker = style["marker"] if style else "o"

                        plt.plot(
                            df["Temperature"],
                            df[prop],
                            marker=marker,
                            label=label,
                            color=color,
                        )
                        has_data = True

                plt.xlabel("Temperature (K)")
                plt.ylabel(ylabel)
                plt.title(f"{prop} vs. Temperature")
                plt.grid(True)
                if has_data:
                    plt.legend()
                plt.tight_layout()
                figs.append(fig)
                if show:
                    plt.show()

    return figs


if __name__ == "__main__":
    # Example usage / Test
    test_samples = {
        "Sample A": "path/to/sample_a.csv",
        "Sample B": "path/to/sample_b.csv",
    }
    # run_multi_sample_analysis(test_samples, "Comparison_Results.xlsx")
