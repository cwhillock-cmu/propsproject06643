import argparse
import sys
import logging

from idaes_props.calculator import (
    calculate_single_property,
    calculate_multiple_properties,
    calculate_properties_range,
)
from idaes_props.plotter import plot_property
from idaes_props.engine import registered_components, validate_component
from pyomo.environ import units as pyunits

logger = logging.getLogger(__name__)

_PRESSURE_UNITS = {
    "Pa": pyunits.Pa,
    "kPa": pyunits.kPa,
    "MPa": pyunits.MPa,
    "bar": pyunits.bar,
    "atm": pyunits.atm,
    "psi": pyunits.psi,
}

_TEMPERATURE_UNITS = {
    "K": pyunits.K,
    "C": "C",
}


def _resolve_pressure_unit(name):
    if name not in _PRESSURE_UNITS:
        raise argparse.ArgumentTypeError(
            f"Unknown pressure unit '{name}'. Choose from: {list(_PRESSURE_UNITS.keys())}"
        )
    return _PRESSURE_UNITS[name]


def _resolve_temperature_unit(name):
    if name not in _TEMPERATURE_UNITS:
        raise argparse.ArgumentTypeError(
            f"Unknown temperature unit '{name}'. Choose from: {list(_TEMPERATURE_UNITS.keys())}"
        )
    return _TEMPERATURE_UNITS[name]


def _parse_float_list(s):
    """Parse a comma-separated string of floats, or a start:stop:step range spec."""
    if ":" in s:
        parts = s.split(":")
        if len(parts) != 3:
            raise argparse.ArgumentTypeError(
                f"Range must be start:stop:step, got '{s}'"
            )
        start, stop, step = float(parts[0]), float(parts[1]), float(parts[2])
        if step <= 0:
            raise argparse.ArgumentTypeError("Step must be positive.")
        vals = []
        v = start
        while v <= stop + step * 1e-9:
            vals.append(round(v, 10))
            v += step
        return vals
    return [float(x.strip()) for x in s.split(",")]


def build_parser():
    parser = argparse.ArgumentParser(
        prog="idaes-props",
        description="Calculate physical properties using the IDAES Helmholtz EOS.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- shared arguments ---
    def add_common_args(p):
        p.add_argument("component", help="Pure component name (e.g. co2, h2o).")
        p.add_argument("-T", "--temperature", type=float, required=True,
                       help="Temperature value.")
        p.add_argument("-P", "--pressure", type=float, required=True,
                       help="Pressure value.")
        p.add_argument("--temperature-unit", default="K",
                       help="Temperature unit: K or C (default: K).")
        p.add_argument("--pressure-unit", default="Pa",
                       help="Pressure unit: Pa, kPa, MPa, bar, atm, psi (default: Pa).")
        p.add_argument("--basis", default="mole", choices=["mole", "mass"],
                       help="Amount basis (default: mole).")

    # --- single ---
    single = subparsers.add_parser("single", help="Calculate a single property at a T-P point.")
    add_common_args(single)
    single.add_argument("property", help="Property name to calculate (e.g. enth_mol, dens_mol).")

    # --- multi ---
    multi = subparsers.add_parser("multi", help="Calculate multiple properties at a T-P point.")
    add_common_args(multi)
    multi.add_argument("--properties", nargs="*", default=None,
                       help="Property names to calculate. Omit for all available properties.")

    # --- range ---
    rng = subparsers.add_parser("range", help="Calculate properties over a T or P range.")
    rng.add_argument("component", help="Pure component name (e.g. co2, h2o).")
    rng.add_argument("-T", "--temperature", required=True,
                     help="Temperature: single value, comma-separated list, or start:stop:step range.")
    rng.add_argument("-P", "--pressure", required=True,
                     help="Pressure: single value, comma-separated list, or start:stop:step range.")
    rng.add_argument("--temperature-unit", default="K",
                     help="Temperature unit: K or C (default: K).")
    rng.add_argument("--pressure-unit", default="Pa",
                     help="Pressure unit: Pa, kPa, MPa, bar, atm, psi (default: Pa).")
    rng.add_argument("--basis", default="mole", choices=["mole", "mass"],
                     help="Amount basis (default: mole).")
    rng.add_argument("--properties", nargs="*", default=None,
                     help="Property names to calculate. Omit for all available properties.")

    # --- plot ---
    plot = subparsers.add_parser("plot", help="Plot a property over a T or P range.")
    plot.add_argument("component", help="Pure component name (e.g. co2, h2o).")
    plot.add_argument("property", help="Property name to plot (e.g. enth_mol, visc_d_phase).")
    plot.add_argument("-T", "--temperature", required=True,
                      help="Temperature: single value, comma-separated list, or start:stop:step range.")
    plot.add_argument("-P", "--pressure", required=True,
                      help="Pressure: single value, comma-separated list, or start:stop:step range.")
    plot.add_argument("--temperature-unit", default="K",
                      help="Temperature unit: K or C (default: K).")
    plot.add_argument("--pressure-unit", default="Pa",
                      help="Pressure unit: Pa, kPa, MPa, bar, atm, psi (default: Pa).")
    plot.add_argument("--basis", default="mole", choices=["mole", "mass"],
                      help="Amount basis (default: mole).")
    plot.add_argument("--output", default=None,
                      help="Output filename. Default: {component}_{property}.png")
    plot.add_argument("--format", default="png", choices=["png", "svg", "pdf"],
                      help="Output file format (default: png).")
    plot.add_argument("--dpi", type=int, default=150,
                      help="Resolution in DPI (default: 150).")

    # --- list-components ---
    subparsers.add_parser("list-components", help="List supported components.")

    # --- list-properties ---
    subparsers.add_parser("list-properties", help="List available property names.")

    return parser


def cmd_single(args):
    t_unit = _resolve_temperature_unit(args.temperature_unit)
    p_unit = _resolve_pressure_unit(args.pressure_unit)
    result = calculate_single_property(
        component=args.component,
        temperature=args.temperature,
        pressure=args.pressure,
        property_name=args.property,
        temperature_unit=t_unit,
        pressure_unit=p_unit,
        amount_basis=args.basis,
    )
    print(f"{args.property} = {result}")


def cmd_multi(args):
    t_unit = _resolve_temperature_unit(args.temperature_unit)
    p_unit = _resolve_pressure_unit(args.pressure_unit)
    df = calculate_multiple_properties(
        component=args.component,
        temperature=args.temperature,
        pressure=args.pressure,
        property_names=args.properties,
        temperature_unit=t_unit,
        pressure_unit=p_unit,
        amount_basis=args.basis,
    )
    print(df.to_string(index=False))


def cmd_range(args):
    t_unit = _resolve_temperature_unit(args.temperature_unit)
    p_unit = _resolve_pressure_unit(args.pressure_unit)
    temperatures = _parse_float_list(args.temperature)
    pressures = _parse_float_list(args.pressure)
    df = calculate_properties_range(
        component=args.component,
        temperatures=temperatures,
        pressures=pressures,
        property_names=args.properties,
        temperature_unit=t_unit,
        pressure_unit=p_unit,
        amount_basis=args.basis,
    )
    print(df.to_string(index=False))


def cmd_plot(args):
    t_unit = _resolve_temperature_unit(args.temperature_unit)
    p_unit = _resolve_pressure_unit(args.pressure_unit)
    temperatures = _parse_float_list(args.temperature)
    pressures = _parse_float_list(args.pressure)

    # Use list directly if multiple values, scalar if single
    if len(temperatures) == 1:
        temperatures = temperatures[0]
    if len(pressures) == 1:
        pressures = pressures[0]

    output = args.output
    if output is None:
        output = f"{args.component}_{args.property}.{args.format}"

    fig, df = plot_property(
        component=args.component,
        property_name=args.property,
        temperatures=temperatures,
        pressures=pressures,
        temperature_unit=t_unit,
        pressure_unit=p_unit,
        amount_basis=args.basis,
        show=False,
        save_path=output,
        dpi=args.dpi,
        fmt=args.format,
    )
    print(f"Plot saved to {output}")


def cmd_list_components(args):
    for c in sorted(registered_components()):
        print(c)


def cmd_list_properties(args):
    import csv
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "available_properties.csv")
    csv_path = os.path.normpath(csv_path)
    if os.path.exists(csv_path):
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                indexed = " (phase-indexed)" if row.get("Indexed by Phase") == "Yes" else ""
                print(f"{row['Name']}{indexed}")
    else:
        print("available_properties.csv not found. Run with a component to inspect stateblock attributes.")


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "single":
            cmd_single(args)
        elif args.command == "multi":
            cmd_multi(args)
        elif args.command == "range":
            cmd_range(args)
        elif args.command == "plot":
            cmd_plot(args)
        elif args.command == "list-components":
            cmd_list_components(args)
        elif args.command == "list-properties":
            cmd_list_properties(args)
    except (ValueError, AttributeError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
