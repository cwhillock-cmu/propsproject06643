import json
import os
import subprocess
import sys

import pandas as pd


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "idaes_props.cli", *args],
        capture_output=True, text=True, timeout=120,
    )


# --- multi command CSV/JSON export ---

def test_multi_csv_export(tmp_path):
    out = str(tmp_path / "multi.csv")
    result = run_cli(
        "multi", "co2", "-T", "298.15", "-P", "101325",
        "--properties", "temperature", "pressure", "enth_mol",
        "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)
    df = pd.read_csv(out)
    assert len(df) == 1
    assert "enth_mol" in df.columns
    assert f"to {out}" in result.stdout


def test_multi_json_export(tmp_path):
    out = str(tmp_path / "multi.json")
    result = run_cli(
        "multi", "co2", "-T", "298.15", "-P", "101325",
        "--properties", "temperature", "pressure", "enth_mol",
        "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)
    with open(out) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 1
    assert "enth_mol" in data[0]


def test_multi_stdout_default(tmp_path):
    """Without --output, multi prints to stdout as before."""
    result = run_cli(
        "multi", "co2", "-T", "298.15", "-P", "101325",
        "--properties", "enth_mol",
    )
    assert result.returncode == 0
    assert "enth_mol" in result.stdout


# --- range command CSV/JSON export ---

def test_range_csv_export(tmp_path):
    out = str(tmp_path / "range.csv")
    result = run_cli(
        "range", "co2", "-T", "280,300,320", "-P", "101325",
        "--properties", "temperature", "pressure", "enth_mol",
        "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)
    df = pd.read_csv(out)
    assert len(df) == 3
    assert "enth_mol" in df.columns


def test_range_json_export(tmp_path):
    out = str(tmp_path / "range.json")
    result = run_cli(
        "range", "co2", "-T", "280,300,320", "-P", "101325",
        "--properties", "temperature", "pressure", "enth_mol",
        "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)
    with open(out) as f:
        data = json.load(f)
    assert len(data) == 3


def test_range_stdout_default():
    """Without --output, range prints to stdout as before."""
    result = run_cli(
        "range", "co2", "-T", "280,300", "-P", "101325",
        "--properties", "enth_mol",
    )
    assert result.returncode == 0
    assert "enth_mol" in result.stdout


# --- error handling ---

def test_export_unsupported_extension(tmp_path):
    out = str(tmp_path / "out.xlsx")
    result = run_cli(
        "multi", "co2", "-T", "298.15", "-P", "101325",
        "--properties", "enth_mol",
        "--output", out,
    )
    assert result.returncode != 0
    assert "Unsupported" in result.stderr or "extension" in result.stderr


def test_export_missing_extension(tmp_path):
    out = str(tmp_path / "noext")
    result = run_cli(
        "multi", "co2", "-T", "298.15", "-P", "101325",
        "--properties", "enth_mol",
        "--output", out,
    )
    assert result.returncode != 0
    assert "extension" in result.stderr
