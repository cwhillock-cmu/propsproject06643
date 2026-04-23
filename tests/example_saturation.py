"""Example: P-T phase diagrams with the saturation curve overlay.

Produces three plots:
1. Single-component CO2 P-T diagram with saturation curve and critical point.
2. Multi-component comparison of CO2 and butane saturation curves.
3. Raw saturation data exported to CSV via the _compute_saturation_curve helper.
"""

import pandas as pd

from idaes_props.plotter import plot_property, _compute_saturation_curve


# 1. Single-component P-T diagram
fig1, df1 = plot_property(
    "co2",
    "pressure_sat",
    temperatures=(220, 304),
    pressures=101325,
    num_points=40,
    saturation=True,
    save_path="co2_pt_diagram.png",
    show=False,
)
print("Single-component plot saved: co2_pt_diagram.png")

# 2. Multi-component P-T comparison
fig2, df2 = plot_property(
    ["co2", "butane"],
    "pressure_sat",
    temperatures=(230, 420),
    pressures=101325,
    num_points=40,
    saturation=True,
    save_path="co2_butane_pt.png",
    show=False,
)
print("Multi-component plot saved: co2_butane_pt.png")

# 3. Export raw saturation data via the helper
curve = _compute_saturation_curve("co2", num_points=30)
print(f"\nCO2 critical point: T = {curve['t_crit']:.2f} K, "
      f"P = {curve['p_crit']:.0f} Pa")

raw = pd.DataFrame({
    "temperature_K": curve["temperatures"],
    "pressure_sat_Pa": curve["pressures"],
})
raw.to_csv("co2_saturation.csv", index=False)
print("Raw saturation data saved: co2_saturation.csv")
print(raw.head())
