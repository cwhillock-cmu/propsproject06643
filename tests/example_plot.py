"""Example: plotting thermodynamic properties with idaes_props."""

from pyomo.environ import units as pyunits
from idaes_props.plotter import plot_property

# 1. Isobaric sweep: molar enthalpy of CO2 from 280-320 K at 1 atm
fig, df = plot_property(
    "co2",
    "enth_mol",
    temperatures=(280, 320),
    pressures=101325,
    num_points=30,
    save_path="co2_enth_mol_isobaric.png",
)
print("Isobaric sweep:")
print(df[["temperature", "phase_id", "enth_mol"]].head())
print()

# 2. Isothermal sweep: mass density of CO2 at 25 C over 1-100 bar
fig2, df2 = plot_property(
    "co2",
    "dens_mass",
    temperatures=25,
    pressures=(1, 100),
    num_points=30,
    temperature_unit="C",
    pressure_unit=pyunits.bar,
    amount_basis="mass",
    save_path="co2_dens_mass_isothermal.svg",
)
print("Isothermal sweep:")
print(df2[["pressure", "phase_id", "dens_mass"]].head())
print()

# 3. Phase-indexed property: dynamic viscosity of water over a phase change
fig3, df3 = plot_property(
    "h2o",
    "visc_d_phase",
    temperatures=(350, 400),
    pressures=101325,
    num_points=20,
    save_path="h2o_viscosity_phase.png",
)
print("Phase-indexed property (h2o viscosity):")
print(df3[["temperature", "phase_id", "visc_d_phase_Vap", "visc_d_phase_Liq"]].head())
