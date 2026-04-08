import os
import pytest
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for tests
import matplotlib.pyplot as plt
import matplotlib.figure
import pandas as pd
from pyomo.environ import units as pyunits

from idaes_props.plotter import plot_property, _expand_range, _plot_from_dataframe


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
    out = str(tmp_path / "test.svg")
    fig, df = plot_property(
        "co2", "enth_mol",
        temperatures=[280, 300, 320],
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
