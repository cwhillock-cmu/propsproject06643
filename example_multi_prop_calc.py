from idaes_props.calculator import calculate_multiple_properties
from pyomo.environ import units
from idaes.models.properties.general_helmholtz import AmountBasis

df = calculate_multiple_properties('co2',temperature=273.15,pressure=120,pressure_unit=units.bar,amount_basis=AmountBasis.MASS)
print(list(df.columns.values))

df2 = calculate_multiple_properties('co2',temperature=293.15,pressure=120,property_names=['mw','temperature','pressure','dens_mass','enth_mass','entr_mass','cp_mass','cv_mass'],pressure_unit=units.bar,amount_basis=AmountBasis.MASS)
print(df2)