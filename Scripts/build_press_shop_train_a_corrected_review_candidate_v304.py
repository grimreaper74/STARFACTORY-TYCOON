"""Correct v037 floor placement and create unobstructed matched review views in an isolated child."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAModularMatchedCamerasCandidate_v303"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainACorrectedReviewCandidate_v304"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAModularMatchedCamerasCandidate_v303.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainACorrectedReviewCandidate_v304.umap"
BASE_SHA = "C69F40D305B8557A33D3E7DE1A55E0D5BC92570BAC8AFC0CBD6FC642B67FEA56"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_corrected_review_build_v304.json"

HIDE_LABELS = {
    "LB_V300_PTA_SEGMENTED_BALANCED_SHELL",
    "LB_PRESS_Column_2000_-5250", "LB_PRESS_Column_4000_-5250",
    "LB_PRESS_Column_2000_-3750", "LB_PRESS_Column_4000_-3750",
    "LB_V301_WIDESPAN_TRANSFER_GIRDER_X6000_Y-5250_TBC",
    "LB_V301_WIDESPAN_TRANSFER_GIRDER_X6000_Y-3750_TBC",
}

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("v303 hash drift")

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v304")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v303 child failed")

actors = actors_api.get_all_level_actors()
candidate = next(
    (a for a in actors if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}),
    None,
)
if candidate is None:
    raise RuntimeError("candidate missing")

before_origin, before_extent = candidate.get_actor_bounds(False)
floor_correction = -(before_origin.z - before_extent.z)
loc = candidate.get_actor_location()
candidate.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z + floor_correction), False, False)
candidate.tags = list(candidate.tags) + [
    unreal.Name("LB.Placement.FloorCorrected.v304"),
    unreal.Name("LB.Asset.Candidate.v304"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

hidden = []
for actor in actors:
    if actor.get_actor_label() in HIDE_LABELS:
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.set_actor_hidden_in_game(True)
        hidden.append(actor.get_actor_label())

def add_ortho(label, location, target, width):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False
    )
    camera.camera_component.set_editor_properties({
        "projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC,
        "ortho_width": width,
        "aspect_ratio": 16 / 9,
        "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name("LB.Camera.Fixed.ProMatched.v304"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    return camera

def add_perspective(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False
    )
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16 / 9,
        "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name("LB.Camera.Fixed.ProMatched.v304"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    return camera

centre = (3873.375, -4199.5, 520.0)
add_ortho("LB_V304_CAM_TrainAOperatorMatched", (3873.375, -5200.0, 520.0), centre, 6200.0)
add_ortho("LB_V304_CAM_TrainARearMatched", (3873.375, -3200.0, 520.0), centre, 6200.0)
add_perspective("LB_V304_CAM_TrainAElevatedMatched", (6900.0, -5350.0, 1550.0), centre, 72.0)

after_origin, after_extent = candidate.get_actor_bounds(False)
failures = []
floor_z = after_origin.z - after_extent.z
if abs(floor_z) > 1.0:
    failures.append(f"candidate floor z {floor_z}")
if not levels.save_current_level():
    failures.append("save failed")
if sha(BASE_FILE) != BASE_SHA:
    failures.append("protected v303 changed")

payload = {
    "$schema": "cairnwell/audit/press-train-a-corrected-review-v304/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FLOOR_CORRECTED_MATCHED_REVIEW_CHILD__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V304_NOT_A_PARENT",
    "base": BASE,
    "base_sha256": BASE_SHA,
    "map": MAP,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "floor_correction_cm": floor_correction,
    "candidate_bounds_after": {
        "origin": [after_origin.x, after_origin.y, after_origin.z],
        "extent": [after_extent.x, after_extent.y, after_extent.z],
        "floor_z": floor_z,
    },
    "review_only_hidden_obstructions": sorted(hidden),
    "review_only_hidden_obstruction_count": len(hidden),
    "runtime_authority_changed": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
