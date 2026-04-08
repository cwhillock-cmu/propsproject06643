from idaes_props.calculator import calculate_properties_range
from pyomo.environ import units

df2 = calculate_properties_range('co2',temperatures=[273.15,283.15,293.15,303.15,313.15],pressures=74,property_names=['temperature','pressure','dens_mass','enth_mass','entr_mass','cp_mass','cv_mass'],pressure_unit=units.bar,amount_basis='mass')
print(df2)

df2 = calculate_properties_range('co2',temperatures=293.15,pressures=[50,51,52,53,54,55,56,57,58,59,60],property_names=['temperature','pressure','dens_mass','enth_mass','entr_mass','cp_mass','cv_mass'],pressure_unit=units.bar,amount_basis='mass')
print(df2)