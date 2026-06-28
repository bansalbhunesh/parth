"""Tests for the real-datasheet pairs and their offline detection guarantee.

These assert against an INDEPENDENTLY authored ground truth (eval manifest +
PROVENANCE), not the seeded synthetic corpus — so a green run here is evidence
the detector works on real third-party values, not just on its own plants.
"""

import pathlib

import pytest

from backend.analyze import _freeform_compare, _resilient_fallback
from eval.real_pairs_offline import MANIFEST
from eval.real_pairs_offline import run as run_offline_eval

REAL = pathlib.Path(__file__).parent.parent / "data" / "samples" / "real"


def _devs(spec_name, sub_name, label):
    spec = (REAL / spec_name).read_text(encoding="utf-8")
    sub = (REAL / sub_name).read_text(encoding="utf-8")
    return _resilient_fallback(spec, sub, label)


def _sigs(devs):
    return {(str(d["required_value"]), str(d["provided_value"])) for d in devs}


def test_floor_pair_offline_catch():
    """Tate ConCore 1250 (1250 lbf) vs 1500 lbf required — a hard datasheet fact."""
    devs = _devs("design_basis_floor.md", "submittal_floor_concore1250.md", "FLOOR")
    assert ("1500", "1250") in _sigs(devs)
    # No false positives: the compliant rolling/pedestal/flame values are NOT flagged.
    assert len(devs) == 1


def test_busway_pair_offline_catch():
    """Schneider Canalis KTA10 (50 kA/1s) vs 65 kA required — a hard datasheet fact."""
    devs = _devs("design_basis_busway.md", "submittal_busway_canalis.md", "BUSWAY")
    assert ("65", "50") in _sigs(devs)
    assert any(d["component"] == "BUSWAY-01" for d in devs)
    assert len(devs) == 1  # IP55>=IP54 and 1000A current are correctly cleared


def test_helios_pair_offline_headlines():
    devs = _devs("design_basis_helios.md", "submittal_gxt5_qsk60.md", "HELIOS")
    s = _sigs(devs)
    assert ("10", "7") in s          # battery autonomy
    assert ("96", "95.9") in s       # online double-conversion efficiency


def test_thermal_contested_not_flagged_offline():
    """The within-allowable 30C setpoint must NOT be a confident offline finding;
    it is a judgment call reserved for the reasoning layer."""
    devs = _devs("design_basis_thermal_setpoint.md", "submittal_crah_setpoint.md", "THERMAL")
    assert devs == []


def test_value_signature_dedup():
    """Two overlapping rules reporting the same required->provided transition must
    collapse to one finding (no double-count of one physical fact)."""
    spec = "**Short-circuit withstand rating.** short-time withstand current 65 kA for 1 s."
    sub = "Rated short-time withstand current 50 kA for 1 s. Short-circuit rating 50 kA."
    devs = _freeform_compare(spec, sub)
    ka = [d for d in devs if (str(d["required_value"]), str(d["provided_value"])) == ("65", "50")]
    assert len(ka) == 1


def test_offline_eval_guarantee_holds():
    """The published offline guarantee — full recall on the offline set, zero
    false positives — must hold; run() returns non-zero if it regresses."""
    assert run_offline_eval() == 0


@pytest.mark.parametrize("pair", MANIFEST, ids=[p["id"] for p in MANIFEST])
def test_real_pair_files_exist(pair):
    assert (REAL / pair["spec"]).exists()
    assert (REAL / pair["submittal"]).exists()
    assert pair["devs"], "every real pair must declare at least one ground-truth deviation"
