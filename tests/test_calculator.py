import pytest
import pyomo.environ as pyo
from pyomo.environ import units as pyunits
from idaes_props.calculator import calculate_single_property
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

