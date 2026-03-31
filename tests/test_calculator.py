import pytest
import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import units as pyunits
from idaes_props.calculator import (
    calculate_single_property,
    calculate_multiple_properties,
    calculate_properties_range,
)
from idaes_props.engine import validate_component

def test_validate_component():
    validate_component("co2")
    validate_component("h2o")
    with pytest.raises(ValueError, match="not supported"):
        validate_component("unobtanium")

def test_calculate_single_property():
    # Test valid calculation
    temp = 298.15
    pres = 101325
    
    # Calculate molar enthalpy
    enth = calculate_single_property("co2", temp, pres, "enth_mol")
    assert isinstance(enth, float)
    
    # Calculate density
    dens = calculate_single_property("co2", temp, pres, "dens_mol")
    assert isinstance(dens, float)
    assert dens > 0

def test_unit_conversion():
    # Calculate at 25 C (298.15 K) and 1 bar (100000 Pa)
    val_k_pa = calculate_single_property("co2", 298.15, 100000, "enth_mol")
    val_c_bar = calculate_single_property(
        "co2", 25.0, 1.0, "enth_mol", 
        temperature_unit="C", 
        pressure_unit=pyunits.bar
    )
    
    # Values should be identical
    assert pytest.approx(val_k_pa, rel=1e-5) == val_c_bar

def test_invalid_temperature():
    with pytest.raises(ValueError, match="Temperature must be greater than 0"):
        calculate_single_property("co2", -5, 101325, "enth_mol")

def test_invalid_pressure():
    with pytest.raises(ValueError, match="Pressure must be greater than 0"):
        calculate_single_property("co2", 298.15, -100, "enth_mol")

def test_invalid_property():
    with pytest.raises(AttributeError, match="not available"):
        calculate_single_property("co2", 298.15, 101325, "nonexistent_prop")

def test_phase_indexed_property():
    with pytest.raises(ValueError, match="phase-indexed property"):
        # dens_mol_phase is indexed by phase
        calculate_single_property("co2", 298.15, 101325, "dens_mol_phase")

from idaes.models.properties.general_helmholtz import AmountBasis

def test_amount_basis_mass():
    # Calculate mass enthalpy and check basis conflict
    val_mass = calculate_single_property("co2", 298.15, 101325, "enth_mass", amount_basis=AmountBasis.MASS)
    assert isinstance(val_mass, float)
    
    with pytest.raises(ValueError, match="is a mole-based property"):
        calculate_single_property("co2", 298.15, 101325, "enth_mol", amount_basis=AmountBasis.MASS)
        
    with pytest.raises(ValueError, match="is a mass-based property"):
        calculate_single_property("co2", 298.15, 101325, "enth_mass", amount_basis=AmountBasis.MOLE)

def test_calculate_multiple_properties():
    # Test getting multiple properties
    props = ['temperature', 'pressure', 'dens_mol_phase', 'enth_mol']
    df = calculate_multiple_properties("co2", 298.15, 101325, property_names=props)
    
    # Check DataFrame characteristics
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    
    # Check columns
    assert 'phase_id' in df.columns
    assert 'temperature' in df.columns
    assert 'pressure' in df.columns
    assert 'dens_mol_phase_Vap' in df.columns
    assert 'dens_mol_phase_Liq' in df.columns
    assert 'enth_mol' in df.columns
    
    # Check values
    assert df.loc[0, 'phase_id'] in ['Vap', 'Liq', 'Mix']
    assert pytest.approx(df.loc[0, 'temperature'],rel=1e-5) == 298.15
    assert df.loc[0, 'pressure'] == 101325
    assert df.loc[0, 'enth_mol'] is not None

def test_calculate_multiple_properties_all():
    # Test getting all properties (property_names=None)
    df = calculate_multiple_properties("co2", 298.15, 101325, property_names=None)

    # Should have a large number of columns
    assert len(df.columns) > 10
    assert 'phase_id' in df.columns
    assert 'mw' in df.columns


def test_multiple_properties_skips_wrong_basis():
    # Requesting mass properties with mole basis should silently skip them
    props = ['enth_mol', 'enth_mass', 'temperature']
    df = calculate_multiple_properties("co2", 298.15, 101325, property_names=props, amount_basis="mole")
    assert 'enth_mol' in df.columns
    assert 'temperature' in df.columns
    # enth_mass should be skipped, not raise
    assert 'enth_mass' not in df.columns


def test_multiple_properties_unknown_property_skipped():
    # Unknown property names should be skipped with a warning, not raise
    props = ['temperature', 'nonexistent_prop']
    df = calculate_multiple_properties("co2", 298.15, 101325, property_names=props)
    assert 'temperature' in df.columns
    assert 'nonexistent_prop' not in df.columns


def test_multiple_properties_string_basis():
    df = calculate_multiple_properties(
        "co2", 298.15, 101325,
        property_names=['enth_mass'],
        amount_basis="mass",
    )
    assert 'enth_mass' in df.columns
    assert isinstance(df.loc[0, 'enth_mass'], float)


# --- Feature 3: calculate_properties_range tests ---

def test_range_isobaric():
    """Isobaric sweep: single pressure, multiple temperatures."""
    temps = [280, 300, 320]
    df = calculate_properties_range(
        "co2", temperatures=temps, pressures=101325,
        property_names=['temperature', 'pressure', 'enth_mol'],
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert 'phase_id' in df.columns
    # Each row should have the same pressure
    for _, row in df.iterrows():
        assert row['pressure'] == 101325
    # Temperatures should be monotonically increasing
    assert list(df['temperature']) == sorted(df['temperature'])


def test_range_isothermal():
    """Isothermal sweep: single temperature, multiple pressures."""
    pressures = [50000, 101325, 200000]
    df = calculate_properties_range(
        "co2", temperatures=298.15, pressures=pressures,
        property_names=['temperature', 'pressure', 'dens_mol'],
    )
    assert len(df) == 3
    # Each row should have approximately the same temperature
    for _, row in df.iterrows():
        assert pytest.approx(row['temperature'], rel=1e-5) == 298.15
    # Density should increase with pressure for an ideal-like gas
    assert df.iloc[0]['dens_mol'] < df.iloc[2]['dens_mol']


def test_range_all_properties():
    """Range calc with property_names=None returns all properties."""
    df = calculate_properties_range(
        "co2", temperatures=[290, 300], pressures=101325,
        property_names=None,
    )
    assert len(df) == 2
    assert len(df.columns) > 10
    assert 'phase_id' in df.columns


def test_range_single_point():
    """A single T-P point should return one row, same as Feature 2."""
    df_range = calculate_properties_range(
        "co2", temperatures=298.15, pressures=101325,
        property_names=['enth_mol'],
    )
    df_multi = calculate_multiple_properties(
        "co2", 298.15, 101325,
        property_names=['enth_mol'],
    )
    assert len(df_range) == 1
    assert pytest.approx(df_range.loc[0, 'enth_mol'], rel=1e-5) == df_multi.loc[0, 'enth_mol']


def test_range_unit_conversion():
    """Range calc should accept non-SI units."""
    df_si = calculate_properties_range(
        "co2", temperatures=[298.15], pressures=[100000],
        property_names=['enth_mol'],
    )
    df_conv = calculate_properties_range(
        "co2", temperatures=[25.0], pressures=[1.0],
        property_names=['enth_mol'],
        temperature_unit="C", pressure_unit=pyunits.bar,
    )
    assert pytest.approx(df_si.loc[0, 'enth_mol'], rel=1e-5) == df_conv.loc[0, 'enth_mol']


def test_range_string_basis():
    """Range calc should accept string amount_basis."""
    df = calculate_properties_range(
        "co2", temperatures=[298.15], pressures=[101325],
        property_names=['enth_mass'],
        amount_basis="mass",
    )
    assert 'enth_mass' in df.columns


def test_range_mismatched_lengths():
    """Mismatched list lengths should raise ValueError."""
    with pytest.raises(ValueError, match="same length"):
        calculate_properties_range("co2", temperatures=[280, 290], pressures=[101325, 200000, 300000])


def test_range_empty():
    """Empty input should raise ValueError."""
    with pytest.raises(ValueError, match="At least one"):
        calculate_properties_range("co2", temperatures=[], pressures=[])


def test_range_invalid_temperature():
    with pytest.raises(ValueError, match="greater than 0 Kelvin"):
        calculate_properties_range("co2", temperatures=[-5, 300], pressures=101325)


def test_range_invalid_pressure():
    with pytest.raises(ValueError, match="greater than 0 Pascal"):
        calculate_properties_range("co2", temperatures=300, pressures=[101325, -100])
