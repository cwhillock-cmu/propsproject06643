import pytest
import pandas as pd
from idaes_props.calculator import calculate_properties_range


def test_skip_failures_all_valid():
    """skip_failures=True with all valid points should return same results as default."""
    temps = [280, 300, 320]
    df_default = calculate_properties_range(
        "co2", temperatures=temps, pressures=101325,
        property_names=['temperature', 'enth_mol'],
    )
    df_skip = calculate_properties_range(
        "co2", temperatures=temps, pressures=101325,
        property_names=['temperature', 'enth_mol'],
        skip_failures=True,
    )
    assert len(df_skip) == 3
    for i in range(3):
        assert pytest.approx(df_skip.loc[i, 'enth_mol'], rel=1e-5) == df_default.loc[i, 'enth_mol']


def test_skip_failures_bad_point():
    """skip_failures=True should skip a T-P point that causes solver failure."""
    temps = [298.15, 298.15]
    pressures = [101325, 1e15]  # second point: absurd pressure
    df = calculate_properties_range(
        "co2", temperatures=temps, pressures=pressures,
        property_names=['temperature', 'pressure', 'enth_mol'],
        skip_failures=True,
    )
    # At least the valid point should be present; the bad one may be skipped
    assert len(df) >= 1
    assert pytest.approx(df.iloc[0]['temperature'], rel=1e-5) == 298.15


def test_skip_failures_false_raises():
    """skip_failures=False (default) should raise on solver failure."""
    temps = [298.15, 298.15]
    pressures = [101325, 1e15]
    with pytest.raises(RuntimeError):
        calculate_properties_range(
            "co2", temperatures=temps, pressures=pressures,
            property_names=['enth_mol'],
            skip_failures=False,
        )
