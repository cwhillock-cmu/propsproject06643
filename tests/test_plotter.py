import os
import pytest
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for tests
import matplotlib.pyplot as plt
import matplotlib.figure
import pandas as pd
from pyomo.environ import units as pyunits

from idaes_props.plotter import (
    plot_property,
    _expand_range,
    _plot_from_dataframe,
    _get_critical_point,
    _compute_saturation_curve,
)
import numpy as np


# --- _expand_range tests ---

def test_expand_range_tuple():
    result = _expand_range((10, 20), num_points=5)
    assert len(result) == 5
    assert result[0] == pytest.approx(10.0)
    assert result[-1] == pytest.approx(20.0)


def test_expand_range_list_passthrough():
    vals = [1.0, 2.0, 3.0]
    assert _expand_range(vals, num_points=50) is vals


def test_expand_range_scalar_passthrough():
    assert _expand_range(42.0, num_points=50) == 42.0


# --- _plot_from_dataframe tests ---

def test_plot_from_dataframe_single_column():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
    fig = _plot_from_dataframe(df, "x", ["y"], "Title", "X", "Y")
    ax = fig.axes[0]
    assert ax.get_title() == "Title"
    assert ax.get_xlabel() == "X"
    assert ax.get_ylabel() == "Y"
    assert len(ax.get_lines()) == 1
    plt.close(fig)


def test_plot_from_dataframe_multiple_columns():
    df = pd.DataFrame({"x": [1, 2], "y_Vap": [10, 20], "y_Liq": [5, 8]})
    fig = _plot_from_dataframe(df, "x", ["y_Vap", "y_Liq"], "T", "X", "Y")
    ax = fig.axes[0]
    assert len(ax.get_lines()) == 2
    plt.close(fig)


def test_plot_from_dataframe_phase_coloring():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
    phase_ids = pd.Series(["Vap", "Vap", "Liq"])
    fig = _plot_from_dataframe(df, "x", ["y"], "T", "X", "Y", phase_ids=phase_ids)
    ax = fig.axes[0]
    # Two lines: one for Vap, one for Liq
    assert len(ax.get_lines()) == 2
    plt.close(fig)


# --- plot_property integration tests ---

def test_plot_property_isobaric():
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
    )
    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "enth_mol" in df.columns
    ax = fig.axes[0]
    assert "isobaric" in ax.get_title()
    assert "Temperature" in ax.get_xlabel()
    plt.close(fig)


def test_plot_property_isothermal():
    fig, df = plot_property(
        "co2", "dens_mol",
        temperatures=298.15,
        pressures=[50000, 101325, 200000],
        show=False,
    )
    assert len(df) == 3
    ax = fig.axes[0]
    assert "isothermal" in ax.get_title()
    assert "Pressure" in ax.get_xlabel()
    plt.close(fig)


def test_plot_property_auto_discretize():
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=(280, 320),
        pressures=101325,
        num_points=7,
        show=False,
    )
    assert len(df) == 7
    plt.close(fig)


def test_plot_property_phase_indexed():
    fig, df = plot_property(
        "co2", "dens_mol_phase",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
    )
    assert "dens_mol_phase_Vap" in df.columns
    assert "dens_mol_phase_Liq" in df.columns
    ax = fig.axes[0]
    # Should have 2 lines (Vap and Liq)
    assert len(ax.get_lines()) == 2
    plt.close(fig)


def test_plot_property_save_file(tmp_path):
    out = str(tmp_path / "test.png")
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
        save_path=out,
    )
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0
    plt.close(fig)


def test_plot_property_save_svg(tmp_path):
    """Extension-based format inference: .svg save_path -> SVG output."""
    out = str(tmp_path / "test.svg")
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
        save_path=out,
    )
    assert os.path.exists(out)
    plt.close(fig)


def test_plot_property_save_missing_extension(tmp_path):
    """save_path without an extension should raise a clear error."""
    out = str(tmp_path / "noext")
    with pytest.raises(ValueError, match="no file extension"):
        plot_property(
            "co2", "enth_mol",
            temperatures=[280, 300],
            pressures=101325,
            show=False,
            save_path=out,
        )


def test_plot_property_save_unsupported_extension(tmp_path):
    """save_path with an unsupported extension should raise a clear error."""
    out = str(tmp_path / "test.jpg")
    with pytest.raises(ValueError, match="Unsupported plot format"):
        plot_property(
            "co2", "enth_mol",
            temperatures=[280, 300],
            pressures=101325,
            show=False,
            save_path=out,
        )


def test_plot_property_explicit_fmt_wins(tmp_path):
    """Explicit fmt argument takes precedence over extension inference."""
    # Filename ends in .png but we force SVG — matplotlib honors explicit format
    out = str(tmp_path / "forced_svg.png")
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[280, 300],
        pressures=101325,
        show=False,
        save_path=out,
        fmt="svg",
    )
    assert os.path.exists(out)
    plt.close(fig)


def test_plot_property_invalid_property():
    with pytest.raises(ValueError, match="produced no data columns"):
        plot_property(
            "co2", "nonexistent_prop",
            temperatures=[280, 300],
            pressures=101325,
            show=False,
        )


def test_plot_property_unit_conversion():
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[0, 25, 50],
        pressures=1,
        temperature_unit="C",
        pressure_unit=pyunits.bar,
        show=False,
    )
    assert len(df) == 3
    plt.close(fig)


# --- multi-component tests ---

def test_plot_multi_component():
    """Multiple components on the same plot."""
    fig, df = plot_property(
        ["co2", "butane"], "dens_mol",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
    )
    assert isinstance(fig, matplotlib.figure.Figure)
    assert "component" in df.columns
    assert set(df["component"].unique()) == {"co2", "butane"}
    assert len(df) == 6  # 3 points x 2 components
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "co2" in labels
    assert "butane" in labels
    assert len(ax.get_lines()) == 2
    plt.close(fig)


def test_plot_multi_component_phase_indexed():
    """Phase-indexed property with multiple components produces line per component+phase."""
    fig, df = plot_property(
        ["co2", "butane"], "dens_mol_phase",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
    )
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "co2 Vap" in labels
    assert "co2 Liq" in labels
    assert "butane Vap" in labels
    assert "butane Liq" in labels
    assert len(ax.get_lines()) == 4
    plt.close(fig)


def test_plot_multi_component_title():
    """Title includes all component names."""
    fig, df = plot_property(
        ["co2", "propane"], "enth_mol",
        temperatures=[280, 320],
        pressures=101325,
        show=False,
    )
    title = fig.axes[0].get_title()
    assert "co2" in title
    assert "propane" in title
    plt.close(fig)


def test_plot_multi_component_save(tmp_path):
    """Multi-component plot saves to file."""
    out = str(tmp_path / "multi.png")
    fig, df = plot_property(
        ["co2", "butane"], "enth_mol",
        temperatures=[280, 300, 320],
        pressures=101325,
        show=False,
        save_path=out,
    )
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0
    plt.close(fig)


def test_plot_single_component_string_still_works():
    """Passing a single string (not list) still works as before."""
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[280, 300],
        pressures=101325,
        show=False,
    )
    assert "component" in df.columns
    assert list(df["component"].unique()) == ["co2"]
    plt.close(fig)


# --- saturation curve tests ---

def test_get_critical_point_co2():
    """CO2 critical point: T_c ~ 304.13 K, P_c ~ 7.38 MPa."""
    t_crit, p_crit = _get_critical_point("co2")
    assert 300 < t_crit < 310
    assert 7e6 < p_crit < 8e6


def test_compute_saturation_curve_monotonic():
    """Saturation curve should be monotonic in both T and P."""
    curve = _compute_saturation_curve("co2", num_points=15)
    t = curve["temperatures"]
    p = curve["pressures"]
    assert len(t) >= 5  # at least some points survived
    assert np.all(np.diff(t) > 0), "T not monotonic"
    assert np.all(np.diff(p) > 0), "P not monotonic"


def test_compute_saturation_curve_endpoints():
    """Curve should start well below and end near the critical point."""
    curve = _compute_saturation_curve("co2", num_points=20)
    t_crit = curve["t_crit"]
    p_crit = curve["p_crit"]
    # Last point should be within 5% of T_crit (we stop at 0.995 * T_crit)
    assert curve["temperatures"][-1] < t_crit
    assert curve["temperatures"][-1] > 0.95 * t_crit
    # Last P should be close to P_crit (within factor of 2, since near-critical behavior is nonlinear)
    assert curve["pressures"][-1] < p_crit
    assert curve["pressures"][-1] > 0.5 * p_crit


def test_compute_saturation_curve_custom_bounds():
    """Explicit t_min and t_max override defaults."""
    curve = _compute_saturation_curve("co2", num_points=10, t_min=250, t_max=300)
    assert curve["temperatures"][0] >= 249.9
    assert curve["temperatures"][-1] <= 300.1


# --- saturation overlay integration tests ---

def test_plot_property_saturation_overlay():
    """Saturation overlay adds a dashed curve and critical point marker."""
    fig, df = plot_property(
        "co2", "pressure_sat",
        temperatures=(240, 300),
        pressures=101325,
        num_points=10,
        saturation=True,
        show=False,
    )
    ax = fig.axes[0]
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "saturation" in labels
    assert "critical point" in labels
    plt.close(fig)


def test_plot_property_saturation_skipped_on_wrong_axes(caplog):
    """Warning logged and overlay skipped when y-axis is not pressure-like."""
    with caplog.at_level("WARNING", logger="idaes_props.plotter"):
        fig, df = plot_property(
            "co2", "enth_mol",
            temperatures=[280, 300, 320],
            pressures=101325,
            saturation=True,
            show=False,
        )
    labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    assert "saturation" not in labels
    assert "critical point" not in labels
    assert any("Saturation overlay skipped" in r.message for r in caplog.records)
    plt.close(fig)


def test_plot_property_saturation_multi_component():
    """Multi-component saturation overlay draws one curve per component."""
    fig, df = plot_property(
        ["co2", "butane"], "pressure_sat",
        temperatures=(250, 400),
        pressures=101325,
        num_points=8,
        saturation=True,
        show=False,
    )
    labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    assert "co2 saturation" in labels
    assert "butane saturation" in labels
    assert "co2 critical point" in labels
    assert "butane critical point" in labels
    plt.close(fig)
