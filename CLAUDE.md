# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python package (`idaes_props`) for calculating thermodynamic properties using the IDAES pure component Helmholtz Equation of State. Uses Pyomo for optimization and IDAES-PSE for property models. Requires the IPOPT solver on PATH.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_calculator.py

# Run a specific test
pytest tests/test_calculator.py::test_calculate_single_property
```

## Architecture

- **`src/idaes_props/engine.py`** — `PropertyEngine` class: builds a Pyomo `ConcreteModel` with a `HelmholtzParameterBlock` configured for P-H (pressure-enthalpy) state variables and LG (liquid-gas) phase presentation. Wraps IPOPT solver. Also contains `validate_component()` which checks against IDAES `registered_components()`.
- **`src/idaes_props/calculator.py`** — Public API with two functions:
  - `calculate_single_property()` — Feature 1: single scalar property at a T-P point. Rejects phase-indexed properties.
  - `calculate_multiple_properties()` — Feature 2: returns a pandas DataFrame with multiple properties (including phase-indexed ones flattened as `prop_Vap`/`prop_Liq` columns) and a `phase_id` column derived from `vapor_frac`.
- **`src/idaes_props/__init__.py`** — Package init with logging setup and IPOPT availability check.
- **`available_properties.csv`** — Reference list of all Helmholtz stateblock properties, their types (Variable/Expression), and whether they are phase-indexed.

## Key Technical Details

- The formulation uses **P-H StateVars** (not T-P), so temperature is set via a Pyomo `Constraint`, not fixed directly. This is more robust for phase equilibrium.
- Temperature unit conversion from Celsius requires `pyomo.environ.units.convert_temp_C_to_K` — standard Pyomo `convert_value` does not handle absolute temperature offsets.
- IPOPT results for fixed state variables have floating-point drift (e.g., 298.1499999900664 vs 298.15). Use `pytest.approx` with relative tolerance in tests.
- Phase-indexed properties (e.g., `dens_mol_phase`) are iterated over their index set and stored as `{name}_{index}` in DataFrames.
- Amount basis (mole vs mass) affects which properties are valid — the calculator skips or rejects mismatched basis properties.

## Current Status

Steps 1–4 complete. Remaining: batch range calculations (Feature 3), comprehensive testing, CLI (`argparse`), and documentation. See `PLAN.txt` for details.
