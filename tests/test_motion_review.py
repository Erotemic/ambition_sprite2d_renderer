from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_authoring import apply_phase_template
from ambition_sprite2d_renderer.authoring.motion_review import review_document, run_motion_review
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


def _walk_doc(slide: float = 0.0) -> RigDocument:
    return RigDocument(
        {
            "name": "walk_probe",
            "frame": {"width": 128, "height": 128, "center_x": 64.0, "ground_y": 104.0, "ankle_h": 2.0},
            "bones": [
                {"name": "pelvis", "parent": None, "offset": [0, -30], "length": 0, "rest_angle": 0},
                {"name": "torso", "parent": "pelvis", "offset": [0, -18], "length": 12, "rest_angle": -90},
                {"name": "head", "parent": "torso", "offset": [12, 0], "length": 6, "rest_angle": 0},
                {"name": "near_leg_u", "parent": "pelvis", "offset": [4, 0], "length": 22, "rest_angle": 80},
                {"name": "near_leg_l", "parent": "near_leg_u", "offset": [22, 0], "length": 22, "rest_angle": 0},
                {"name": "near_leg_foot", "parent": "near_leg_l", "offset": [22, 0], "length": 6, "rest_angle": 0},
                {"name": "far_leg_u", "parent": "pelvis", "offset": [-4, 0], "length": 22, "rest_angle": 100},
                {"name": "far_leg_l", "parent": "far_leg_u", "offset": [22, 0], "length": 22, "rest_angle": 0},
                {"name": "far_leg_foot", "parent": "far_leg_l", "offset": [22, 0], "length": 6, "rest_angle": 0},
            ],
            "parts": [],
            "ik_legs": [
                {"upper": "near_leg_u", "lower": "near_leg_l", "foot": "near_leg_foot", "channel_prefix": "near_foot", "rest_x": 10, "rest_lift": 0, "bend": 1},
                {"upper": "far_leg_u", "lower": "far_leg_l", "foot": "far_leg_foot", "channel_prefix": "far_foot", "rest_x": -10, "rest_lift": 0, "bend": -1},
            ],
            "ik_chains": [],
            "clips": {
                "walk": {
                    "loop": True,
                    "frames": 8,
                    "duration_ms": 100,
                    "channels": {
                        # Near foot stays grounded but optionally slides.
                        "near_foot_x": {"keys": [[0.0, 10, "linear"], [0.875, 10 + slide, "linear"]]},
                        "near_foot_lift": {"const": 0},
                        "far_foot_x": {"const": -10},
                        "far_foot_lift": {"keys": [[0.0, 8], [0.5, 0], [0.875, 8]]},
                        "root_y": {"expr": "2*sin(tau*t)"},
                    },
                }
            },
        }
    )


def test_motion_review_reports_foot_slide_and_pelvis_excursion():
    doc = _walk_doc(slide=9.0)
    apply_phase_template(doc, "walk", "walk")
    review = review_document(doc, "walk", target="walk_probe", travel_px_per_cycle=0.0)
    assert review.metrics["near_foot_slide"]["worst_local_rms_px"] > 1.0
    assert review.metrics["pelvis"]["vertical_excursion_px"] > 0.0
    assert any(finding.code == "foot_slide" for finding in review.findings)
    assert review.metrics["phase_roles"]["0"] == "contact_near"


def test_run_motion_review_writes_json_markdown_and_image(tmp_path: Path):
    doc = _walk_doc(slide=0.0)
    apply_phase_template(doc, "walk", "walk")
    rig = tmp_path / "walk_probe.rig.json"
    doc.save(rig)
    review = run_motion_review(target="walk_probe", clip_name="walk", rig_path=rig, out_dir=tmp_path / "review")
    assert review.output_paths["json"].exists()
    assert review.output_paths["markdown"].exists()
    assert review.output_paths["image"].exists()
    assert review.output_paths["paths"].exists()
    assert "Endpoint speed" not in review.output_paths["markdown"].read_text()  # report is concise, graph owns dense series


def test_motion_review_resolves_published_carl_rig_without_rebuilding(tmp_path):
    from ambition_sprite2d_renderer.authoring.motion_rig_resolver import find_existing_rig_document
    from ambition_sprite2d_renderer.authoring.motion_review import run_motion_review

    resolved = find_existing_rig_document("carl_stargan")
    assert resolved.name == "carl_stargan_side.rig.json"

    review = run_motion_review(
        target="carl_stargan",
        clip_name="walk",
        out_dir=tmp_path,
    )
    assert review.rig_path.resolve() == resolved
    assert (tmp_path / "motion_review.json").is_file()
    assert (tmp_path / "motion_review.png").is_file()
