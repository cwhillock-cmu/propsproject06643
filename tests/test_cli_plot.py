import os
import subprocess
import sys
import pytest


def run_cli(*args):
    """Run idaes-props CLI and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "idaes_props.cli", *args],
        capture_output=True, text=True, timeout=120,
    )


def test_plot_produces_file(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli("plot", "co2", "enth_mol", "-T", "280:320:20", "-P", "101325", "--output", out)
    assert result.returncode == 0
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0


def test_plot_default_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_cli("plot", "co2", "enth_mol", "-T", "280,300,320", "-P", "101325")
    assert result.returncode == 0
    expected = tmp_path / "co2_enth_mol.png"
    assert expected.exists()


def test_plot_svg_format(tmp_path):
    out = str(tmp_path / "out.svg")
    result = run_cli("plot", "co2", "enth_mol", "-T", "280,300,320", "-P", "101325", "--output", out)
    assert result.returncode == 0
    assert os.path.exists(out)


def test_plot_pdf_format(tmp_path):
    out = str(tmp_path / "out.pdf")
    result = run_cli("plot", "co2", "enth_mol", "-T", "280,300,320", "-P", "101325", "--output", out)
    assert result.returncode == 0
    assert os.path.exists(out)


def test_plot_unsupported_extension(tmp_path):
    out = str(tmp_path / "out.jpg")
    result = run_cli("plot", "co2", "enth_mol", "-T", "280,300", "-P", "101325", "--output", out)
    assert result.returncode != 0
    assert "Unsupported" in result.stderr or "extension" in result.stderr


def test_plot_with_units(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli(
        "plot", "co2", "dens_mass", "-T", "25", "-P", "1,5,10",
        "--temperature-unit", "C", "--pressure-unit", "bar",
        "--basis", "mass", "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)


def test_plot_phase_indexed(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli("plot", "co2", "dens_mol_phase", "-T", "280,300,320", "-P", "101325", "--output", out)
    assert result.returncode == 0
    assert os.path.exists(out)


def test_plot_invalid_component(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli("plot", "unobtanium", "enth_mol", "-T", "280,300", "-P", "101325", "--output", out)
    assert result.returncode != 0
    assert "Error" in result.stderr


def test_plot_missing_args():
    result = run_cli("plot", "co2", "enth_mol")
    assert result.returncode != 0


# --- multi-component CLI tests ---

def test_plot_multi_component(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli(
        "plot", "co2", "dens_mol", "-T", "280,300,320", "-P", "101325",
        "--components", "butane", "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0


def test_plot_multi_component_three(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli(
        "plot", "co2", "enth_mol", "-T", "280,300,320", "-P", "101325",
        "--components", "butane", "propane", "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)


def test_plot_multi_component_default_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_cli(
        "plot", "co2", "enth_mol", "-T", "280,300,320", "-P", "101325",
        "--components", "butane",
    )
    assert result.returncode == 0
    expected = tmp_path / "co2_butane_enth_mol.png"
    assert expected.exists()


def test_plot_multi_component_phase_indexed(tmp_path):
    out = str(tmp_path / "out.png")
    result = run_cli(
        "plot", "co2", "dens_mol_phase", "-T", "280,300,320", "-P", "101325",
        "--components", "butane", "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)


# --- saturation overlay CLI ---

def test_plot_saturation_flag(tmp_path):
    out = str(tmp_path / "sat.png")
    result = run_cli(
        "plot", "co2", "pressure_sat", "-T", "240:300:10", "-P", "101325",
        "--saturation", "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)


def test_plot_saturation_wrong_axes(tmp_path):
    """--saturation with non-P-T plot should still succeed (overlay skipped silently)."""
    out = str(tmp_path / "sat_wrong.png")
    result = run_cli(
        "plot", "co2", "enth_mol", "-T", "280:320:10", "-P", "101325",
        "--saturation", "--output", out,
    )
    assert result.returncode == 0
    assert os.path.exists(out)
