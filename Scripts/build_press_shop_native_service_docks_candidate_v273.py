"""Fresh direct-v269 four-dock native candidate; never mutates the protected parent."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
PROJECT = Path(unreal.Paths.project_dir()).resolve()
PROTECTED = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269.umap"
AUDIT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_native_service_docks_build_v273.json"

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP):
    raise RuntimeError(f"fresh-map invariant failed: {MAP}")
protected_before = sha256(PROTECTED)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"failed to create {MAP}")

dock_specs = {
    "LB-DOCK-MR01-01": unreal.LBServiceDockVariant.MR01_MAINTENANCE,
    "LB-DOCK-MR01-02": unreal.LBServiceDockVariant.MR01_MAINTENANCE,
    "LB-DOCK-CR01-01": unreal.LBServiceDockVariant.CR01_CLEANING,
    "LB-DOCK-CR01-02": unreal.LBServiceDockVariant.CR01_CLEANING,
}
dock_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBSupportRobotServiceDock")
installed = []
for label, variant in dock_specs.items():
    old = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
    if not isinstance(old, unreal.StaticMeshActor):
        raise RuntimeError(f"retained aggregate missing: {label}")
    transform = old.get_actor_transform()
    old_mesh = old.static_mesh_component.static_mesh.get_path_name() if old.static_mesh_component.static_mesh else None
    if not actors.destroy_actor(old):
        raise RuntimeError(f"failed to remove aggregate {label}")
    dock = actors.spawn_actor_from_class(dock_class, transform.translation, transform.rotation.rotator())
    dock.set_actor_scale3d(transform.scale3d)
    dock.set_actor_label(label)
    dock.tags = [unreal.Name("LB.Asset.Candidate.ServiceDock.Native.v273"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Dock.Native.GuardedRuntime")]
    if not dock.configure_dock(label, variant):
        raise RuntimeError(f"failed to configure {label}")
    installed.append({"label": label, "variant": str(variant), "location_cm": [transform.translation.x, transform.translation.y, transform.translation.z], "removed_mesh": old_mesh})

removed_proxies = []
for label in dock_specs:
    for suffix in ("Collision_WestSide", "Collision_EastSide", "Collision_Rear"):
        proxy_label = f"{label}_{suffix}"
        proxy = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == proxy_label), None)
        if proxy is None or not actors.destroy_actor(proxy):
            raise RuntimeError(f"failed to remove superseded proxy {proxy_label}")
        removed_proxies.append(proxy_label)

for family, x in (("MR01", -5795.0), ("CR01", -895.0)):
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(x, 3000, 430), unreal.Rotator())
    camera.set_actor_label(f"LB_DOCK_V273_CAM_{family}_PAIR")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(x, 5160, 90)), False)
    camera.camera_component.set_editor_properties({"field_of_view": 48.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.Camera.Fixed.ServiceDockCandidate.v273")]

if not levels.save_current_level():
    raise RuntimeError("failed to save v273")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("protected v269 changed")
map_file = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-native-service-docks-build-v273/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_DIRECT_V269_FOUR_NATIVE_DOCK_CANDIDATE__GATES_OPEN__NOT_PROMOTED",
    "map": MAP,
    "map_sha256": sha256(map_file),
    "parent": BASE,
    "installed": installed,
    "removed_proxy_blockers": removed_proxies,
    "protected_v269_sha256_before": protected_before,
    "protected_v269_sha256_after": protected_after,
    "promotion_authorized": False
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_NATIVE_SERVICE_DOCKS_BUILD_V273_PASS")
