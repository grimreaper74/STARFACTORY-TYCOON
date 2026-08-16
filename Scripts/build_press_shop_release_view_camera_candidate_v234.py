"""Create a camera-only v234 successor from retained shell direction v233."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v234"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_release_view_camera_build_v234.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233.umap"
CAMERAS = [
    ("LB_WHOLE_V234_CAM_FrontEndElevated", (-10100.0, 5100.0, 1580.0), (-6100.0, -1900.0, 260.0), 63.0),
    ("LB_WHOLE_V234_CAM_TrainBaysElevated", (9700.0, 5100.0, 1580.0), (5200.0, -1750.0, 310.0), 65.0),
    ("LB_WHOLE_V234_CAM_CentralAisle", (-600.0, 5000.0, 920.0), (6900.0, -800.0, 520.0), 61.0),
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
    camera.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.WholeShop.v234"),
        unreal.Name("LB.Asset.Candidate.v234"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    created.append({"label": label, "location_cm": list(location), "target_cm": list(target), "fov": fov})

if len(created) != 3:
    failures.append(f"expected three cameras, created {len(created)}")
if not levels.save_current_level():
    failures.append("could not save v234")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v233 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v234.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-release-view-camera-build-v234/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__THREE_CAMERA_ONLY_RELEASE_VIEWS_BUILT__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "cameras": created,
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
