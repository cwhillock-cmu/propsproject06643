# IDAES Properties

A Python package and CLI tool for calculating thermodynamic properties of pure components using the IDAES Helmholtz Equation of State (EOS).

Given a component, temperature, and pressure, this tool calculates properties such as enthalpy, entropy, density, heat capacity, speed of sound, viscosity, and thermal conductivity. Results are returned as floats or pandas DataFrames.

## Installation

Requires Python 3.9+ and the [IPOPT](https://coin-or.github.io/Ipopt/) solver on your system PATH.

```bash
pip install -e ".[dev]"
```

To verify IPOPT is available:

```bash
ipopt --version
```

If IPOPT is missing, the package will emit a `RuntimeWarning` at import time.

## How It Works

This tool wraps the [IDAES](https://idaes-pse.readthedocs.io/) Helmholtz EOS property library, which implements high-accuracy equations of state for pure components. Under the hood, each property calculation:

1. **Creates a Pyomo ConcreteModel** -- [Pyomo](https://www.pyomo.org/) is an algebraic modeling language for optimization. A `ConcreteModel` is the container that holds all variables, constraints, and objectives.

2. **Adds a HelmholtzParameterBlock** -- This IDAES block defines the thermodynamic model for a specific pure component (e.g., CO2, water). It is configured with:
   - `phase_presentation=PhaseType.LG` (liquid-gas equilibrium)
   - `state_vars=StateVars.PH` (pressure-enthalpy formulation)
   - An `amount_basis` of either mole or mass

3. **Builds a state block** -- A state block is created from the parameter block. This is where the actual thermodynamic state (T, P, phase fractions, all properties) lives. Multiple state blocks can be added to a single model to solve many T-P points at once.

4. **Fixes pressure and constrains temperature** -- Because the formulation uses pressure-enthalpy (P-H) state variables, pressure is fixed directly as a variable, while temperature is set through a Pyomo `Constraint`. The P-H formulation is more numerically robust than T-P around phase boundaries.

5. **Solves with IPOPT** -- The model is solved using the IPOPT nonlinear optimizer. IPOPT finds the enthalpy value that satisfies the temperature constraint, and all other properties (density, entropy, heat capacity, etc.) are then available as Pyomo expressions on the state block.

6. **Extracts property values** -- After the solve, `pyo.value()` is called on the desired variables and expressions to extract numerical results.

For batch calculations (Feature 3), multiple state blocks are added to a single model and solved in one IPOPT call, which is more efficient than solving each point individually.

## Supported Components

`butane`, `co2`, `h2o`, `isobutane`, `propane`, `r1234ze`, `r125`, `r134a`, `r227ea`, `r32`

You can also query this at runtime:

```python
from idaes.models.properties.general_helmholtz import registered_components
print(registered_components())
```

Or from the CLI:

```bash
idaes-props list-components
```

## Python API

### `calculate_single_property`

Calculates a single scalar property at a temperature-pressure point.

```python
from idaes_props.calculator import calculate_single_property

# Molar enthalpy of CO2 at 298.15 K, 1 atm
enth = calculate_single_property("co2", temperature=298.15, pressure=101325, property_name="enth_mol")
print(enth)  # 22261.99 J/mol

# With unit conversion and mass basis
dens = calculate_single_property(
    "co2",
    temperature=25,
    pressure=1,
    property_name="dens_mass",
    temperature_unit="C",       # Celsius -> converted to Kelvin internally
    pressure_unit=units.bar,    # bar -> converted to Pa internally
    amount_basis="mass",        # accepts "mass", "mole", or AmountBasis enum
)
```

**Parameters:**
- `component` (str) -- Pure component name (e.g. `"co2"`, `"h2o"`)
- `temperature` (float) -- Temperature value
- `pressure` (float) -- Pressure value
- `property_name` (str) -- Name of the property to calculate (e.g. `"enth_mol"`, `"dens_mass"`, `"cp_mol"`)
- `temperature_unit` -- `pyunits.K` (default), or `"C"` for Celsius
- `pressure_unit` -- `pyunits.Pa` (default), or any Pyomo pressure unit (`pyunits.bar`, `pyunits.atm`, etc.)
- `amount_basis` -- `"mole"` (default), `"mass"`, or an `AmountBasis` enum value

**Returns:** `float`

**Note:** Phase-indexed properties (like `dens_mol_phase`) are not supported by this function. Use `calculate_multiple_properties` instead.

### `calculate_multiple_properties`

Calculates multiple properties at a single temperature-pressure point, returning a one-row pandas DataFrame.

```python
from idaes_props.calculator import calculate_multiple_properties

# Specific properties
df = calculate_multiple_properties(
    "co2",
    temperature=298.15,
    pressure=101325,
    property_names=["temperature", "pressure", "enth_mol", "dens_mol_phase", "cp_mol"],
)
print(df)
# phase_id  temperature  pressure     enth_mol  dens_mol_phase_Vap  dens_mol_phase_Liq    cp_mol
#      Vap       298.15  101325.0  22261.987059           41.081075        16134.945484  37.44581

# All available properties (property_names=None)
df_all = calculate_multiple_properties("h2o", temperature=373.15, pressure=101325)
print(df_all.columns.tolist())  # dozens of columns
```

**Parameters:** Same as `calculate_single_property`, except:
- `property_names` (list or None) -- List of property names, or `None` for all available properties

**Returns:** `pd.DataFrame` (single row)

The DataFrame includes a `phase_id` column (`"Vap"`, `"Liq"`, or `"Mix"`) derived from the vapor fraction. Phase-indexed properties are flattened into separate columns (e.g. `dens_mol_phase_Vap`, `dens_mol_phase_Liq`). Properties that don't match the amount basis are silently skipped.

### `calculate_properties_range`

Calculates properties over a range of temperatures and/or pressures, returning a multi-row DataFrame.

```python
from idaes_props.calculator import calculate_properties_range

# Isobaric sweep: vary temperature at fixed pressure
df = calculate_properties_range(
    "co2",
    temperatures=[280, 290, 300, 310, 320],
    pressures=101325,
    property_names=["temperature", "pressure", "dens_mol", "enth_mol"],
)
print(df)
# phase_id  temperature  pressure  dens_mol     enth_mol
#      Vap        280.0  101325.0  43.79532  21589.306439
#      Vap        290.0  101325.0  42.25620  21958.205868
#      Vap        300.0  101325.0  40.82354  22331.333921
#      Vap        310.0  101325.0  39.48639  22708.671396
#      Vap        320.0  101325.0  38.23531  23090.182038

# Isothermal sweep: vary pressure at fixed temperature
df = calculate_properties_range(
    "co2",
    temperatures=298.15,
    pressures=[50000, 101325, 200000, 500000],
    property_names=["temperature", "pressure", "dens_mol"],
)

# With non-SI units
df = calculate_properties_range(
    "co2",
    temperatures=[0, 10, 20, 30, 40],
    pressures=74,
    property_names=["temperature", "pressure", "dens_mass", "enth_mass", "cp_mass"],
    temperature_unit="C",
    pressure_unit=units.bar,
    amount_basis="mass",
)
```

**Parameters:** Same as `calculate_multiple_properties`, except:
- `temperatures` -- Single value or list of temperature values
- `pressures` -- Single value or list of pressure values

If one is a single value and the other is a list, the single value is broadcast. Both can be lists of equal length for arbitrary T-P pairs.

**Returns:** `pd.DataFrame` (one row per T-P point)

### `plot_property`

Plots a thermodynamic property over a temperature or pressure range. Returns a matplotlib `Figure` and the underlying `DataFrame`.

```python
from idaes_props.plotter import plot_property

# Isobaric sweep: enthalpy of CO2 from 280 K to 320 K at 1 atm
fig, df = plot_property(
    "co2",
    "enth_mol",
    temperatures=(280, 320),   # (start, stop) tuple auto-discretized
    pressures=101325,
    num_points=30,
)

# Isothermal sweep with non-SI units, saved to file
fig, df = plot_property(
    "co2",
    "dens_mass",
    temperatures=25,
    pressures=(1, 100),
    num_points=50,
    temperature_unit="C",
    pressure_unit=units.bar,
    amount_basis="mass",
    save_path="co2_density.png",
    show=False,
)

# Phase-indexed property: plots separate lines for Vap and Liq
fig, df = plot_property(
    "co2",
    "visc_d_phase",
    temperatures=(280, 450),
    pressures=100,
    pressure_unit=units.bar,
)

# Multiple components on one plot
fig, df = plot_property(
    ["co2", "butane"],
    "dens_mol",
    temperatures=(280, 400),
    pressures=101325,
    num_points=30,
)

# Multiple components with a phase-indexed property
fig, df = plot_property(
    ["co2", "butane"],
    "dens_mol_phase",
    temperatures=[280, 300, 320],
    pressures=101325,
    save_path="comparison.png",
    show=False,
)

# P-T phase diagram with the saturation curve and critical point overlay
fig, df = plot_property(
    "co2",
    "pressure_sat",
    temperatures=(220, 304),
    pressures=101325,
    saturation=True,
    save_path="co2_pt_diagram.png",
    show=False,
)
```

**Parameters:**
- `component` (str or list of str) -- Pure component name, or a list of components to overlay on the same plot
- `property_name` (str) -- Property to plot on the y-axis
- `temperatures` -- Fixed value (float), explicit list, or `(start, stop)` tuple for auto-discretization
- `pressures` -- Fixed value (float), explicit list, or `(start, stop)` tuple for auto-discretization
- `num_points` (int) -- Number of points when auto-discretizing a `(start, stop)` range (default: 50)
- `temperature_unit` -- `pyunits.K` (default), or `"C"` for Celsius
- `pressure_unit` -- `pyunits.Pa` (default), or any Pyomo pressure unit
- `amount_basis` -- `"mole"` (default) or `"mass"`
- `show` (bool) -- If True (default), display the plot with `plt.show()`
- `save_path` (str or None) -- If provided, save the figure to this path
- `dpi` (int) -- Resolution for saved figures (default: 150)
- `fmt` (str or None) -- File format: `"png"`, `"svg"`, or `"pdf"`. If `None` (default), inferred from the `save_path` extension.
- `saturation` (bool) -- If True, overlay the liquid-vapor saturation curve and mark the critical point. Only meaningful for P-T plots (y in `pressure`, `pressure_sat`, `pressure_crit`); skipped with a warning otherwise.

**Returns:** `(matplotlib.figure.Figure, pd.DataFrame)`

When multiple components are provided, the returned DataFrame includes a `component` column. Each component is plotted with a distinct color. For phase-indexed properties with multiple components, line style distinguishes phase (solid=Vap, dashed=Liq) while color distinguishes component.

For a single component, non-indexed properties are colored by phase (red=Vap, blue=Liq, purple=Mix). Phase-indexed properties are plotted as separate lines per phase.

### `_compute_saturation_curve` -- Raw Saturation-Curve Data

Lower-level helper that returns the temperature-pressure coordinates of a component's liquid-vapor saturation curve, plus its critical point. Useful if you want the data without a plot (custom styling, CSV export, classifying T-P points as sub- or super-critical).

```python
from idaes_props.plotter import _compute_saturation_curve

curve = _compute_saturation_curve("co2", num_points=50)
print(curve["t_crit"])        # 304.13 K
print(curve["p_crit"])        # 7377300 Pa
print(curve["temperatures"])  # np.ndarray of K (monotonically increasing)
print(curve["pressures"])     # np.ndarray of Pa (monotonically increasing)
```

**Parameters:** `component`, `amount_basis` (`"mole"` default), `num_points` (default 50), `t_min` (default `0.55 * T_crit`), `t_max` (default `0.995 * T_crit`).

**Returns:** `dict` with keys `"temperatures"`, `"pressures"`, `"t_crit"`, `"p_crit"`.

The curve is the locus of T-P points where liquid and vapor phases coexist in equilibrium, bounded below by the triple point and above by the critical point. The defaults clip the endpoints away from the critical singularity; points below the triple point are silently skipped when IPOPT cannot converge there. The returned arrays will typically be shorter than `num_points` — this is expected.

## CLI Usage

After installation, the `idaes-props` command is available. It has six subcommands.

### `single` -- Calculate a Single Property

```bash
idaes-props single co2 -T 298.15 -P 101325 enth_mol
# enth_mol = 22261.987058686685

idaes-props single h2o -T 100 -P 1 --temperature-unit C --pressure-unit atm enth_mass --basis mass
# enth_mass = 2675687.338...
```

### `multi` -- Calculate Multiple Properties

```bash
# Specific properties
idaes-props multi co2 -T 298.15 -P 101325 --properties temperature pressure enth_mol dens_mol cp_mol

# All available properties
idaes-props multi co2 -T 298.15 -P 101325

# Export to CSV instead of printing
idaes-props multi co2 -T 298.15 -P 101325 --output result.csv

# Export to JSON
idaes-props multi co2 -T 298.15 -P 101325 --output result.json
```

### `range` -- Calculate Properties Over a Range

Temperatures and pressures accept three formats:
- Single value: `298.15`
- Comma-separated list: `280,290,300,310,320`
- Start:stop:step range: `280:320:10`

```bash
# Isobaric sweep
idaes-props range co2 -T 280:320:10 -P 101325 --properties temperature pressure enth_mol dens_mol

# Isothermal sweep with non-SI units
idaes-props range co2 -T 25 -P 1,2,3,4,5 --temperature-unit C --pressure-unit bar --properties temperature pressure dens_mass --basis mass

# Export sweep to CSV
idaes-props range co2 -T 280:320:10 -P 101325 --properties temperature pressure enth_mol --output sweep.csv
```

For both `multi` and `range`, `--output <filename>` writes the DataFrame to disk instead of stdout. The format is inferred from the extension: `.csv` or `.json`. Any other extension is rejected with a clear error.

### `plot` -- Plot a Property Over a Range

Generates a plot of a property over a temperature or pressure sweep and saves it to a file. Supports overlaying multiple components on the same plot.

```bash
# Isobaric sweep: enthalpy vs temperature
idaes-props plot co2 enth_mol -T 280:320:10 -P 101325

# Isothermal sweep with units, saved as SVG
idaes-props plot co2 dens_mass -T 25 -P 1,5,10,50,100 --temperature-unit C --pressure-unit bar --basis mass --output co2_density.svg

# Phase-indexed property
idaes-props plot co2 visc_d_phase -T 280:450:10 -P 10000000

# Multiple components on one plot
idaes-props plot co2 dens_mol -T 280:400:20 -P 101325 --components butane

# Three components compared
idaes-props plot co2 enth_mol -T 280:400:20 -P 101325 --components butane propane --output comparison.png

# P-T phase diagram with saturation curve and critical point
idaes-props plot co2 pressure_sat -T 220:304:2 -P 101325 --saturation --output co2_pt_diagram.png

# Multi-component P-T comparison with saturation curves
idaes-props plot co2 pressure_sat -T 220:420:10 -P 101325 --components butane --saturation --output pt_compare.png
```

| Option | Values | Default | Description |
|---|---|---|---|
| `--components` | space-separated names | none | Additional components to overlay |
| `--output` | filename with extension (`.png`, `.svg`, `.pdf`) | `{component}_{property}.png` | Output file path; format is inferred from the extension |
| `--dpi` | integer | `150` | Resolution for raster formats |
| `--saturation` | flag | off | Overlay the liquid-vapor saturation curve and mark the critical point. Only meaningful for P-T plots (see below). |

#### `--saturation`: Overlaying the Phase Boundary

The `--saturation` flag draws the liquid-vapor saturation curve on top of the sweep and marks the critical point with an `X`. Use it when you want to see the phase boundary on a P-T diagram.

**When it applies:** the flag takes effect only when the plot's axes form a pressure-vs-temperature diagram. Concretely, that means sweeping temperature (`-T` is a range, `-P` is a single value) with the property set to `pressure`, `pressure_sat`, or `pressure_crit`. Typical usage plots `pressure_sat` against `-T`.

For any other combination (e.g. `enth_mol` vs T, or density vs P) the flag is accepted silently but the overlay is skipped — a warning is logged explaining why, and the rest of the plot is unaffected.

**What's drawn:**
- A dashed curve tracing vapor pressure vs temperature from roughly `0.55 * T_crit` up to just below `T_crit` (the near-critical region is clipped because the solver degrades there)
- An `X` marker at the critical point itself
- In multi-component plots (`--components ...`), one dashed curve and one critical-point marker per component, each colored to match its data series

**How to read the result:** above the saturation curve the fluid is liquid, below it is vapor, and to the right of the critical point marker it is supercritical with no meaningful phase distinction. If your sweep crosses the curve, you can see exactly where the component transitions between phases. Points below the triple point are automatically skipped, so short curves are expected for components where the triple point is far from the critical point.

### `list-components` -- List Supported Components

```bash
idaes-props list-components
```

### `list-properties` -- List Available Property Names

```bash
idaes-props list-properties
```

### CLI Options

| Option | Values | Default | Description |
|---|---|---|---|
| `--temperature-unit` | `K`, `C` | `K` | Input temperature unit |
| `--pressure-unit` | `Pa`, `kPa`, `MPa`, `bar`, `atm`, `psi` | `Pa` | Input pressure unit |
| `--basis` | `mole`, `mass` | `mole` | Amount basis for properties |
| `--properties` | space-separated names | all | Which properties to calculate (multi/range only) |

## Available Properties

A full list is in `available_properties.csv`. Common properties include:

| Property | Phase-Indexed | Description |
|---|---|---|
| `temperature` | No | Temperature (K) |
| `pressure` | No | Pressure (Pa) |
| `enth_mol` / `enth_mass` | No | Specific enthalpy |
| `entr_mol` / `entr_mass` | No | Specific entropy |
| `dens_mol` / `dens_mass` | No | Density (aggregate) |
| `cp_mol` / `cp_mass` | No | Isobaric heat capacity |
| `cv_mol` / `cv_mass` | No | Isochoric heat capacity |
| `energy_internal_mol` / `_mass` | No | Specific internal energy |
| `heat_capacity_ratio` | No | Cp/Cv ratio |
| `mw` | No | Molecular weight |
| `vapor_frac` | No | Vapor fraction |
| `dens_mol_phase` / `_mass_phase` | Yes | Phase-specific density |
| `cp_mol_phase` / `_mass_phase` | Yes | Phase-specific heat capacity |
| `speed_sound_phase` | Yes | Speed of sound |
| `visc_d_phase` | Yes | Dynamic viscosity |
| `therm_cond_phase` | Yes | Thermal conductivity |
| `surface_tension` | No | Surface tension |

Phase-indexed properties produce separate columns for each phase (e.g. `dens_mol_phase_Vap`, `dens_mol_phase_Liq`).

Properties ending in `_mol` are available when `amount_basis="mole"`, and those ending in `_mass` when `amount_basis="mass"`.

## Running Tests

```bash
# Python unit tests
pytest

# With coverage (matches CI)
pytest --cov=idaes_props --cov-report=term
```

Continuous integration runs on every push and PR to `main` via `.github/workflows/tests.yml` on `windows-latest` with Python 3.13.

## Recent Changes

- **`plot --format` removed.** The plot CLI subcommand no longer accepts `--format`; pass the full filename (with extension) to `--output` instead. Supported extensions: `.png`, `.svg`, `.pdf`. Unknown extensions now produce a clear error.
- **`multi` and `range` gained `--output`.** Export DataFrames to `.csv` or `.json` by filename; omit the flag to keep the existing print-to-stdout behavior.
- **`plot` gained `--saturation`.** Overlays the liquid-vapor saturation curve and critical-point marker on P-T plots. See the `plot` subcommand docs above.
