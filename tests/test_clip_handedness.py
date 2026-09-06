"""The handedness checker must catch an inverted clip, and must not pass on nothing.

⛔⛔ IT PASSED ON NOTHING. `check_sheet` returned no findings when the generated
`*_spritesheet.yaml` was absent, and the default target population is a glob over
those same generated files — which are gitignored. So on a clean checkout the
checker printed `OK: 0 sheet(s), every clip reaches forward` and exited 0, and
naming a target explicitly did the same thing while counting the request.

⭐ THESE TESTS USE A FIXTURE, not the generated art, so the invariant has an
automated road that does not depend on somebody having run the renderer first —
which was the other half of the problem: nothing executed this checker at all.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest
import yaml

_CHECKER = (
    pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check_clip_handedness.py"
)
_spec = importlib.util.spec_from_file_location("check_clip_handedness", _CHECKER)
handedness = importlib.util.module_from_spec(_spec)
sys.modules["check_clip_handedness"] = handedness
_spec.loader.exec_module(handedness)


def _publish(
    sheet_dir: pathlib.Path,
    target: str,
    *,
    poly: list[tuple[float, float]],
    faces_left: bool,
) -> None:
    """A minimal published sheet: a body box, one clip's hull, and a handedness."""
    (sheet_dir / f"{target}_spritesheet.yaml").write_text(
        yaml.safe_dump(
            {
                "body_metrics": {
                    # Centre at (100, 100).
                    "body_pixel_bbox": {"x": 80, "y": 60, "w": 40, "h": 80},
                    "animations": {"attack_side": {"hitbox": {"poly": list(poly)}}},
                }
            }
        )
    )
    (sheet_dir / f"{target}_spritesheet.ron").write_text(
        f"(authored_faces_left: {'true' if faces_left else 'false'},)"
    )


# A hull well ahead of a body whose centre_x is 100, and its mirror image.
AHEAD_OF_A_RIGHT_FACING_BODY = [(140.0, 90.0), (170.0, 90.0), (170.0, 110.0), (140.0, 110.0)]
BEHIND_A_RIGHT_FACING_BODY = [(30.0, 90.0), (60.0, 90.0), (60.0, 110.0), (30.0, 110.0)]


@pytest.mark.parametrize("faces_left", [False, True])
def test_a_clip_reaching_the_way_its_sheet_faces_is_clean(tmp_path, faces_left):
    poly = BEHIND_A_RIGHT_FACING_BODY if faces_left else AHEAD_OF_A_RIGHT_FACING_BODY
    _publish(tmp_path, "fixture", poly=poly, faces_left=faces_left)
    assert handedness.check_sheet(tmp_path, "fixture", False, required=True) == []


@pytest.mark.parametrize("faces_left", [False, True])
def test_a_clip_reaching_backwards_is_a_finding(tmp_path, faces_left):
    """The Officer's defect: a whole hull behind the body that throws it.

    ⛔ BOTH HANDEDNESSES, because the bug was a sheet drawn WEST whose specs all
    claimed EAST — a rule that only knows one direction cannot see that.
    """
    poly = AHEAD_OF_A_RIGHT_FACING_BODY if faces_left else BEHIND_A_RIGHT_FACING_BODY
    _publish(tmp_path, "fixture", poly=poly, faces_left=faces_left)
    findings = handedness.check_sheet(tmp_path, "fixture", False, required=True)
    assert len(findings) == 1, findings
    assert "BEHIND the body" in findings[0]


def test_a_named_target_with_no_published_sheet_is_a_finding(tmp_path):
    """Absence is not success for something somebody asked about."""
    findings = handedness.check_sheet(tmp_path, "absent", False, required=True)
    assert len(findings) == 1
    assert "not generated" in findings[0]


def test_a_sheet_nobody_asked_about_may_be_unrigged(tmp_path):
    """⚠ And the converse, which is why `required` exists rather than a blanket
    failure: the default population is every published sheet and most are not
    rigged fighters. Failing those would make the checker permanently red."""
    assert handedness.check_sheet(tmp_path, "absent", False, required=False) == []


def test_a_run_that_discovers_no_sheets_at_all_fails(tmp_path, capsys, monkeypatch):
    """The whole-run half of the same defect: an empty glob is not a pass."""
    monkeypatch.setattr(
        sys, "argv", ["check_clip_handedness.py", "--assets", str(tmp_path)]
    )
    assert handedness.main() == 1
    assert "had nothing to read" in capsys.readouterr().out
