import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyomo.environ import units as pyunits

from idaes_props.calculator import calculate_properties_range

logger = logging.getLogger(__name__)

PHASE_COLORS = {"Vap": "tab:red", "Liq": "tab:blue", "Mix": "tab:purple"}


def plot_property(
    component: str,
    property_name: str,
    temperatures,
    pressures,
    num_points: int = 50,
    temperature_unit=pyunits.K,
    pressure_unit=pyunits.Pa,
    amount_basis="mole",
    show: bool = True,
    save_path: str = None,
    dpi: int = 150,
    fmt: str = "png",
) -> tuple:
    """Plot a thermodynamic property over a temperature or pressure range.

    Parameters
    ----------
    component : str
        Pure component name (e.g. "co2", "h2o").
    property_name : str
        Property to plot on the y-axis (e.g. "enth_mol", "dens_mol_phase").
    temperatures : float, list, or 2-tuple
        Fixed temperature (float), explicit list of values, or (start, stop)
        tuple to auto-discretize with *num_points*.
    pressures : float, list, or 2-tuple
        Fixed pressure (float), explicit list of values, or (start, stop)
        tuple to auto-discretize with *num_points*.
    num_points : int
        Number of points when auto-discretizing a (start, stop) range.
    temperature_unit : Pyomo unit or "C"
        Unit for temperature values. Default ``pyunits.K``.
    pressure_unit : Pyomo unit
        Unit for pressure values. Default ``pyunits.Pa``.
    amount_basis : str or AmountBasis
        "mole" (default) or "mass".
    show : bool
        If True, call ``plt.show()`` before returning.
    save_path : str or None
        If provided, save the figure to this path.
    dpi : int
        Resolution for saved figures.
    fmt : str
        File format when saving ("png", "svg", "pdf").

    Returns
    -------
    (matplotlib.figure.Figure, pandas.DataFrame)
        The figure and the underlying data.
    """
    # Expand (start, stop) tuples into linspace arrays
    temperatures = _expand_range(temperatures, num_points)
    pressures = _expand_range(pressures, num_points)

    # Determine sweep direction
    t_is_swept = isinstance(temperatures, (list, np.ndarray)) and not isinstance(pressures, (list, np.ndarray))
    p_is_swept = isinstance(pressures, (list, np.ndarray)) and not isinstance(temperatures, (list, np.ndarray))

    if t_is_swept:
        x_column = "temperature"
        t_unit_label = "C" if temperature_unit == "C" else "K"
        x_label = f"Temperature ({t_unit_label})"
        fixed_val = pressures
        sweep_label = f"isobaric, P={fixed_val}"
    elif p_is_swept:
        x_column = "pressure"
        x_label = "Pressure (Pa)"
        fixed_val = temperatures
        sweep_label = f"isothermal, T={fixed_val}"
    else:
        # Both are lists or both are scalars — default to temperature as x
        x_column = "temperature"
        t_unit_label = "C" if temperature_unit == "C" else "K"
        x_label = f"Temperature ({t_unit_label})"
        sweep_label = "T-P sweep"

    # Build the list of properties to request from the calculator
    calc_props = [x_column, property_name]
    if x_column == "pressure" and "temperature" not in calc_props:
        calc_props.append("temperature")

    # Calculate data
    df = calculate_properties_range(
        component,
        temperatures=temperatures,
        pressures=pressures,
        property_names=calc_props,
        temperature_unit=temperature_unit,
        pressure_unit=pressure_unit,
        amount_basis=amount_basis,
        skip_failures=True,
    )

    if df.empty:
        raise RuntimeError(
            f"All T-P points failed to solve for {component}. "
            "Check that the range is within valid bounds."
        )

    # Identify y-columns: phase-indexed properties produce prop_Vap / prop_Liq columns
    y_columns = [c for c in df.columns if c == property_name or c.startswith(property_name + "_")]
    # Exclude the bare property name if phase-indexed columns exist
    phase_cols = [c for c in y_columns if c != property_name]
    if phase_cols:
        y_columns = phase_cols

    if not y_columns:
        raise ValueError(
            f"Property '{property_name}' produced no data columns. "
            "Check that the property name is valid and matches the amount basis."
        )

    title = f"{property_name} of {component} ({sweep_label})"
    y_label = property_name

    fig = _plot_from_dataframe(
        df, x_column, y_columns, title, x_label, y_label,
        phase_ids=df.get("phase_id"),
    )

    if save_path:
        fig.savefig(save_path, format=fmt, dpi=dpi, bbox_inches="tight")
        logger.info(f"Plot saved to {save_path}")

    if show:
        plt.show()

    return fig, df


def _expand_range(value, num_points: int):
    """Convert a (start, stop) tuple into a numpy linspace array.

    If *value* is already a list or array, return it unchanged.
    If *value* is a scalar, return it unchanged (broadcast by the calculator).
    """
    if isinstance(value, (list, np.ndarray)):
        return value
    if isinstance(value, tuple) and len(value) == 2:
        return np.linspace(value[0], value[1], num_points).tolist()
    return value


def _plot_from_dataframe(df, x_column, y_columns, title, x_label, y_label, phase_ids=None):
    """Create a matplotlib figure from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Data to plot.
    x_column : str
        Column name for the x-axis.
    y_columns : list of str
        Column name(s) for the y-axis. Multiple columns produce multiple lines.
    title : str
        Plot title.
    x_label : str
        X-axis label.
    y_label : str
        Y-axis label.
    phase_ids : pd.Series or None
        If provided, color non-phase-indexed series by phase.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    x = df[x_column]

    if len(y_columns) > 1:
        # Multiple y-columns = phase-indexed property; one line per phase
        for col in y_columns:
            # Extract phase suffix (e.g. "Vap" from "dens_mol_phase_Vap")
            phase = col.rsplit("_", 1)[-1]
            color = PHASE_COLORS.get(phase, None)
            ax.plot(x, df[col], marker="o", markersize=3, label=phase, color=color)
    elif phase_ids is not None:
        # Single y-column: color segments by phase
        col = y_columns[0]
        plotted_phases = set()
        for phase in phase_ids.unique():
            mask = phase_ids == phase
            color = PHASE_COLORS.get(phase, None)
            label = phase if phase not in plotted_phases else None
            ax.plot(
                x[mask], df[col][mask],
                marker="o", markersize=3, linestyle="-",
                color=color, label=label,
            )
            plotted_phases.add(phase)
    else:
        ax.plot(x, df[y_columns[0]], marker="o", markersize=3)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if ax.get_legend_handles_labels()[1]:
        ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    return fig
