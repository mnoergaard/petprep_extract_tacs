import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from petprep_extract_tacs import extract_tacs


def _run_cli(monkeypatch, args_list):
    """Run CLI with patched main to capture arguments."""
    called = {}

    def fake_main(args):
        called["args"] = args

    monkeypatch.setattr(extract_tacs, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["extract_tacs"] + args_list)
    extract_tacs.cli()
    return called["args"]


def test_cli_pvc_agtm(monkeypatch, tmp_path):
    bids_dir = tmp_path / "bids"
    out_dir = tmp_path / "out"
    args = [str(bids_dir), str(out_dir), "participant", "--pvc", "agtm", "--psf", "3"]
    parsed = _run_cli(monkeypatch, args)
    assert parsed.pvc == "agtm"
    assert parsed.psf == 3.0


def test_cli_pvc_gtm(monkeypatch, tmp_path):
    bids_dir = tmp_path / "bids"
    out_dir = tmp_path / "out"
    args = [str(bids_dir), str(out_dir), "participant", "--pvc", "gtm"]
    parsed = _run_cli(monkeypatch, args)
    assert parsed.pvc == "gtm"
    assert parsed.psf is None


def test_cli_psf_requires_agtm(monkeypatch, tmp_path):
    bids_dir = tmp_path / "bids"
    out_dir = tmp_path / "out"
    args = [str(bids_dir), str(out_dir), "participant", "--psf", "3"]
    monkeypatch.setattr(sys, "argv", ["extract_tacs"] + args)
    with pytest.raises(SystemExit):
        extract_tacs.cli()


def test_cli_agtm_requires_psf(monkeypatch, tmp_path):
    bids_dir = tmp_path / "bids"
    out_dir = tmp_path / "out"
    args = [str(bids_dir), str(out_dir), "participant", "--pvc", "agtm"]
    monkeypatch.setattr(sys, "argv", ["extract_tacs"] + args)
    with pytest.raises(SystemExit):
        extract_tacs.cli()
