"""Multi-Sample comparison plotting adapter.

This module owns figure construction and visual styling. It receives the
already-calculated sample frames and contains no scientific calculations.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import scienceplots  # noqa: F401 — registers the legacy style names


def plot_comparisons(processed_samples, settings=None, show=True):
    """Generate comparison figures with the established plot contract.

    Returns figures when ``show=False`` for the desktop dialog to display.
    Property names, defaults, layout calculations, styles, and labels mirror
    the former ``src.core.analyzer`` implementation.
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
