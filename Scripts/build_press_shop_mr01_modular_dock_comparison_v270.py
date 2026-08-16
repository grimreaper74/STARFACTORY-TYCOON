"""Fresh direct-v269 child replacing only MR01-01 dock for in-hall comparison."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v270"
PROJECT = Path(unreal.Paths.project_dir()).resolve()
PROTECTED = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269.umap"
AUDIT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_mr01_modular_dock_comparison_build_v270.json"

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP):
    raise RuntimeError(f"fresh-map invariant failed: {MAP}")
protected_before = sha256(PROTECTED)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"failed to create direct child {MAP} from {BASE}")

old = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == "LB-DOCK-MR01-01"), None)
if not isinstance(old, unreal.StaticMeshActor):
    raise RuntimeError("installed MR01-01 aggregate control not found")
old_transform = old.get_actor_transform()
old_mesh = old.static_mesh_component.static_mesh.get_path_name() if old.static_mesh_component.static_mesh else None
old_tags = [str(tag) for tag in old.tags]
if not actors.destroy_actor(old):
    raise RuntimeError("failed to remove only MR01-01 aggregate visual")

dock_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBSupportRobotServiceDock")
replacement = actors.spawn_actor_from_class(dock_class, old_transform.translation, old_transform.rotation.rotator())
replacement.set_actor_scale3d(old_transform.scale3d)
replacement.set_actor_label("LB-DOCK-MR01-01")
replacement.tags = [unreal.Name("LB.Asset.Candidate.ServiceDock.ModularRuntime.v270"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Dock.Comparison.SingleBerthOnly")]
if not replacement.configure_dock("LB-DOCK-MR01-01", unreal.LBServiceDockVariant.MR01_MAINTENANCE):
    raise RuntimeError("replacement dock configuration failed")

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-5795, 3000, 430), unreal.Rotator())
camera.set_actor_label("LB_DOCK_V270_CAM_MR01_PAIR_COMPARISON")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(-5795, 5160, 90)), False)
camera.camera_component.set_editor_properties({"field_of_view": 48.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
camera.tags = [unreal.Name("LB.Camera.Fixed.ServiceDockComparison.v270")]

if not levels.save_current_level():
    raise RuntimeError("failed to save v270")
map_file = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v270.umap"
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("protected v269 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-mr01-modular-dock-comparison-build-v270/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_DIRECT_V269_SINGLE_DOCK_COMPARISON_CHILD__TECHNICAL_AND_VISUAL_GATES_OPEN__NOT_PROMOTED",
    "map": MAP, "map_sha256": sha256(map_file), "parent": BASE,
    "replacement": {
        "label": replacement.get_actor_label(), "class": replacement.get_class().get_path_name(),
        "dock_id": "LB-DOCK-MR01-01", "transform": {
            "location_cm": [old_transform.translation.x, old_transform.translation.y, old_transform.translation.z],
            "rotation_deg": [old_transform.rotation.rotator().pitch, old_transform.rotation.rotator().yaw, old_transform.rotation.rotator().roll],
        },
        "removed_aggregate_mesh": old_mesh, "removed_aggregate_tags": old_tags,
    },
    "control": "LB-DOCK-MR01-02 remains the retained Resolved_v006 aggregate under identical inherited hall lighting",
    "camera": camera.get_actor_label(),
    "protected_v269_sha256_before": protected_before,
    "protected_v269_sha256_after": protected_after,
    "promotion_authorized": False
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_MR01_MODULAR_DOCK_COMPARISON_V270_PASS")
