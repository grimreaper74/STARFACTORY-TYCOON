"""Create four column-aware inspection cameras as a fresh v236 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v237"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_column_aware_camera_build_v237.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v237.umap"

# The inherited structural grid uses X = ... 4000, 6000 ... and Y rows every
# 1500 cm.  Cross-aisle train views therefore use X=5000, midway between two
# column lines, instead of hiding or moving valid hall structure.
CAMERAS = [
    ("LB_WHOLE_V237_CAM_TrainsNorthCrossAisle", (5000.0, 5550.0, 900.0), (5000.0, -1750.0, 390.0), 54.0),
    ("LB_WHOLE_V237_CAM_TrainsSouthCrossAisle", (5000.0, -5700.0, 820.0), (5000.0, -1550.0, 390.0), 54.0),
    ("LB_WHOLE_V237_CAM_TrainLineEastAisle", (9600.0, 1450.0, 720.0), (4550.0, -1750.0, 360.0), 58.0),
    ("LB_WHOLE_V237_CAM_FrontEndProcess", (-9900.0, 4300.0, 1250.0), (-4300.0, -1500.0, 330.0), 60.0),
]

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

created = []
failures = []
for label, location, target, fov in CAMERAS:
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        failures.append(f"could not create {label}")
        continue
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.ColumnAware.v237",
        "LB.Asset.Candidate.v237", "LB.Asset.CandidateNotPromoted")]
    created.append({"label": label, "location_cm": list(location), "target_cm": list(target), "fov": fov})

if len(created) != len(CAMERAS):
    failures.append(f"expected {len(CAMERAS)} cameras, created {len(created)}")
if not levels.save_current_level():
    failures.append("could not save v237")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v236 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-column-aware-camera-build-v237/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_COLUMN_AWARE_CAMERA_ONLY_VIEWS__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "cameras": created,
    "camera_grid_basis": "cross-aisle views use X=5000 cm between inherited structural column lines X=4000 and X=6000 cm",
    "non_camera_actor_changes": 0,
    "geometry_material_light_authority_machine_collision_navigation_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
