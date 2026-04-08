import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyomo.environ import units as pyunits

from idaes_props.calculator import calculate_properties_range

logger = logging.getLogger(__name__)


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
    raise NotImplementedError("plot_property is not yet implemented")


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
        If provided, color points by phase.

    Returns
    -------
    matplotlib.figure.Figure
    """
    raise NotImplementedError("_plot_from_dataframe is not yet implemented")
