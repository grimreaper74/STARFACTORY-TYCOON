"""Fresh direct-v300 operator-side structural-clearance experiment.

Removes only the six hall columns at X=6000 cm across the press-train zone and
adds visual long-span transfer girders between the retained X=4000/8000 rows.
The 40 m span is presentation TBC, not certified engineering authority.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_wide_span_clearance_build_v301.json"
EXPECTED_BASE_SHA = "93BF6B46BAD2292019E31C08EF31AF9C9C21CE98BAB9A045CF7670AF5A7AA52C"
Y_ROWS = [-5250, -3750, -2250, -750, 750, 2250]
REMOVE_LABELS = [f"LB_PRESS_Column_6000_{y}" for y in Y_ROWS]
CAMERAS = [
    ("LB_V301_CAM_TrainAOperatorClear", (6500.0, -5350.0, 510.0), (4380.0, -4650.0, 430.0), 56.0),
    ("LB_V301_CAM_TrainAFlowClear", (6600.0, -5050.0, 760.0), (4200.0, -4550.0, 500.0), 61.0),
    ("LB_V301_CAM_FourTrainWideSpan", (7000.0, -5650.0, 1450.0), (4200.0, -1800.0, 430.0), 67.0),
]

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v301")
if sha256(BASE_FILE) != EXPECTED_BASE_SHA:
    raise RuntimeError("v300 hash drift")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v300 child failed")

by_label = {actor.get_actor_label(): actor for actor in api.get_all_level_actors()}
removed = []
column_material = None
for label in REMOVE_LABELS:
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"missing audited column {label}")
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or str(component.get_collision_profile_name()) != "BlockAll":
        raise RuntimeError(f"unexpected column authority {label}")
    if column_material is None:
        column_material = component.get_material(0)
    removed.append({"label": label, "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z]})
    if not api.destroy_actor(actor):
        raise RuntimeError(f"could not remove {label}")

cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("engine cube missing")
girders = []
for y in Y_ROWS:
    girder = api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(6000.0, float(y), 1740.0), unreal.Rotator())
    if girder is None:
        raise RuntimeError(f"girder spawn failed {y}")
    girder.set_actor_label(f"LB_V301_WIDESPAN_TRANSFER_GIRDER_X6000_Y{y:+05d}_TBC")
    component = girder.static_mesh_component
    component.set_static_mesh(cube)
    girder.set_actor_scale3d(unreal.Vector(40.0, 0.60, 1.20))
    if column_material:
        component.set_material(0, column_material)
    component.set_collision_profile_name(unreal.Name("NoCollision"), True)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("generate_overlap_events", False)
    component.set_editor_property("can_ever_affect_navigation", False)
    girder.tags = [unreal.Name("LB.Structure.WideSpanTransferGirder.TBC"), unreal.Name("LB.Asset.Candidate.v301"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.PresentationOnly.NoEngineeringAuthority")]
    girders.append(girder.get_actor_label())

camera_labels = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        raise RuntimeError(label)
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.WideSpan.v301"), unreal.Name("LB.Asset.Candidate.v301"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera_labels.append(label)

remaining_labels = {actor.get_actor_label() for actor in api.get_all_level_actors()}
train_counts = {key: sum(1 for actor in api.get_all_level_actors() if f"LB.PressTrain.Installed.TRAIN_{key}" in {str(tag) for tag in actor.tags}) for key in "ABCD"}
failures = []
if any(label in remaining_labels for label in REMOVE_LABELS):
    failures.append("one or more target columns remain")
if len(removed) != 6 or len(girders) != 6:
    failures.append(f"structural experiment count mismatch removed={len(removed)} girders={len(girders)}")
if train_counts != {"A": 338, "B": 337, "C": 337, "D": 337}:
    failures.append(f"press train actor contract changed {train_counts}")
if len(camera_labels) != 3:
    failures.append("camera count mismatch")
if not levels.save_current_level():
    failures.append("save failed")
if sha256(BASE_FILE) != EXPECTED_BASE_SHA:
    failures.append("protected v300 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-wide-span-clearance-build-v301/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_OPERATOR_SIDE_COLUMN_ROW_REMOVED_WITH_TBC_VISUAL_GIRDERS__VISUAL_AND_ALL_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V301_NOT_A_PARENT",
    "base": BASE,
    "map": MAP,
    "base_sha256": EXPECTED_BASE_SHA,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "source_audit": "Saved/Audits/PressShopIntegration/press_shop_structural_column_inventory_v300.json",
    "removed_columns": removed,
    "added_visual_girders": girders,
    "span_tbc_cm": 4000.0,
    "structural_certification": "TBC_NOT_ENGINEERING_AUTHORITY",
    "girder_collision": "NoCollision",
    "girder_affects_navigation": False,
    "press_train_actor_counts": train_counts,
    "evidence_cameras": camera_labels,
    "promotion_authorized": false,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
