from pyomo.environ import units as pyunits
from idaes_props.plotter import plot_property

fig, df = plot_property(
    "co2",
    "visc_d_phase",
    #temperatures=(280, 450),
    #pressures=74,
    temperatures=298,
    pressures=(1.01325,100),
    pressure_unit=pyunits.bar,
    num_points=30,
    save_path="co2_viscosity_100bar.png",
)

#print(df[["temperature", "phase_id", "visc_d_phase_Vap", "visc_d_phase_Liq"]].to_string(index=False))
