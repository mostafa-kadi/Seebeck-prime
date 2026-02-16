import matplotlib.pyplot as plt
import scienceplots

# Define some common plot styles to be used across the project
PLOT_STYLES = {
    "style": ["science", "notebook"],
    "figure.figsize": (10, 6),
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "lines.linewidth": 2,
    "lines.markersize": 6,
}


def apply_plot_styles():
    """Apply the common plot styles globally."""
    plt.style.use(PLOT_STYLES["style"])
    plt.rcParams.update(
        {
            "figure.figsize": PLOT_STYLES["figure.figsize"],
            "axes.titlesize": PLOT_STYLES["axes.titlesize"],
            "axes.labelsize": PLOT_STYLES["axes.labelsize"],
            "xtick.labelsize": PLOT_STYLES["xtick.labelsize"],
            "ytick.labelsize": PLOT_STYLES["ytick.labelsize"],
            "legend.fontsize": PLOT_STYLES["legend.fontsize"],
            "lines.linewidth": PLOT_STYLES["lines.linewidth"],
            "lines.markersize": PLOT_STYLES["lines.markersize"],
        }
    )


def plot_line(x, y, title=None, xlabel=None, ylabel=None, legend=None):
    """Create a line plot with the common styles applied."""
    apply_plot_styles()
    plt.figure()
    plt.plot(x, y, marker="o")
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if legend:
        plt.legend(legend)
    plt.tight_layout()
    plt.show()


def plot_scatter(x, y, title=None, xlabel=None, ylabel=None, hue=None):
    """Create a scatter plot with matplotlib and common styles."""
    apply_plot_styles()
    plt.figure()
    if hue is not None:
        plt.scatter(x, y, c=hue)
    else:
        plt.scatter(x, y)
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    plt.tight_layout()
    plt.show()


def plot_multisample(data_list, title=None, xlabel=None, ylabel=None):
    """
    Create a comparison plot for multiple samples using scienceplots.

    Args:
        data_list (list): List of dicts with keys 'x', 'y', 'label'.
        title (str, optional): Plot title.
        xlabel (str, optional): X-axis label.
        ylabel (str, optional): Y-axis label.
    """
    apply_plot_styles()
    plt.figure()
    for item in data_list:
        plt.plot(item["x"], item["y"], label=item.get("label"), marker="o")
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.show()


# Additional advanced plotting functions can be added here as needed
