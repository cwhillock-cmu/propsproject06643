from idaes_props.calculator import calculate_single_property
from pyomo.environ import units
from idaes.models.properties.general_helmholtz import AmountBasis

print(calculate_single_property('co2',temperature=273.15,pressure=120,property_name='dens_mass',pressure_unit=units.bar,amount_basis=AmountBasis.MASS))