import logging
import pyomo.environ as pyo
from pyomo.environ import units as pyunits
from idaes.models.properties.general_helmholtz import AmountBasis
from idaes_props.engine import PropertyEngine

logger = logging.getLogger(__name__)

def convert_to_si(value: float, unit, target_unit):
    """
    Validates and converts a value to the target SI unit using Pyomo's unit library.
    """
    if unit is None or unit == target_unit:
        return value
        
    if target_unit == pyunits.K and unit == "C":
        return pyunits.convert_temp_C_to_K(value)
        
    return pyunits.convert_value(value, from_units=unit, to_units=target_unit)

def calculate_single_property(
    component: str, 
    temperature: float, 
    pressure: float, 
    property_name: str, 
    temperature_unit=pyunits.K, 
    pressure_unit=pyunits.Pa,
    amount_basis=AmountBasis.MOLE
) -> float:
    """
    Feature 1: Calculates a single available property for a given component at a T-P state.
    """
    # 1. Validate property name against amount basis
    if amount_basis == AmountBasis.MOLE and property_name.endswith("_mass"):
        raise ValueError(f"Property '{property_name}' is a mass-based property but amount_basis is MOLE.")
    if amount_basis == AmountBasis.MASS and property_name.endswith("_mol"):
        raise ValueError(f"Property '{property_name}' is a mole-based property but amount_basis is MASS.")

    # 2. Input Validation & Unit Conversion
    try:
        T_si = convert_to_si(temperature, temperature_unit, pyunits.K)
        P_si = convert_to_si(pressure, pressure_unit, pyunits.Pa)
    except Exception as e:
        logger.error(f"Unit conversion failed: {e}")
        raise ValueError(f"Invalid units provided: {e}")
        
    if T_si <= 0:
        raise ValueError("Temperature must be greater than 0 Kelvin.")
    if P_si <= 0:
        raise ValueError("Pressure must be greater than 0 Pascal.")

    # 3. Engine Setup
    engine = PropertyEngine(component, amount_basis=amount_basis)
    model = engine.model
    
    # 4. Create State Block
    # Need to remove existing blocks if engine is reused, but here it's fresh
    model.stateblock1 = model.properties.build_state_block(
        defined_state=True, has_phase_equilibrium=True
    )
    model.obj = pyo.Objective(expr=0)
    
    # Fix extensive variable based on amount_basis
    if amount_basis == AmountBasis.MOLE:
        model.stateblock1.flow_mol.fix(1)
    elif amount_basis == AmountBasis.MASS:
        model.stateblock1.flow_mass.fix(1)
    
    # 5. Set T-P constraints for P-H formulation
    model.stateblock1.pressure.fix(P_si)
    model.T_constraint = pyo.Constraint(expr=model.stateblock1.temperature == T_si)
    
    # 6. Solve
    success = engine.solve()
    if not success:
        raise RuntimeError(f"Failed to solve state for {component} at T={T_si} K, P={P_si} Pa")
        
    # 7. Retrieve Property
    state = model.stateblock1
    if not hasattr(state, property_name):
        raise AttributeError(f"Property '{property_name}' is not available on the stateblock.")
        
    prop_obj = getattr(state, property_name)
    
    # Check if the property is indexed by phase (e.g., dens_mol_phase)
    if prop_obj.is_indexed():
        # Feature 1 specifically requests "a property". For phase-indexed, this is ambiguous 
        # without feature 2's phase_id logic, so we might need the aggregate property instead, 
        # or we return a dict of phase values.
        # For simplicity in Feature 1, we expect a scalar aggregate property like 'enth_mol'.
        raise ValueError(f"'{property_name}' is a phase-indexed property. Feature 1 supports aggregate properties (e.g., enth_mol, entr_mol).")
        
    return pyo.value(prop_obj)
