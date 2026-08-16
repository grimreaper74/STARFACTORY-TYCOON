"""Create a clean visual successor of technical support-fleet checkpoint v255."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v256"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v256.umap"
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_visual_build_v256.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LIB = unreal.EditorAssetLibrary

RESOLVED = {
    "MR01": "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_MR01_ServiceDock_ResolvedMaterials_v006",
    "CR01": "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_CR01_ServiceDock_ResolvedMaterials_v006",
}
CAMERAS = {
    "mr01": {
        "old": "LB_SUPPORT_FLEET_CAM_MR01_v255",
        "new": "LB_SUPPORT_FLEET_CAM_MR01_v256",
        "location": (-5800.0, 3500.0, 330.0),
        "target": (-5800.0, 5160.0, 82.0),
        "fov": 65.0,
    },
    "cr01": {
        "old": "LB_SUPPORT_FLEET_CAM_CR01_v255",
        "new": "LB_SUPPORT_FLEET_CAM_CR01_v256",
        "location": (-900.0, 3500.0, 320.0),
        "target": (-900.0, 5160.0, 76.0),
        "fov": 58.0,
    },
    "overview": {
        "old": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v255",
        "new": "LB_SUPPORT_FLEET_CAM_OVERVIEW_v256",
        "location": (-3300.0, 1000.0, 2500.0),
        "target": (-3300.0, 5000.0, 30.0),
        "fov": 82.0,
    },
}
LIGHT_ROOTS = (
    ("MR01_01", -6495.0, 5160.0),
    ("MR01_02", -5095.0, 5160.0),
    ("CR01_01", -1495.0, 5160.0),
    ("CR01_02", -295.0, 5160.0),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if LIB.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite {MAP}")
base_hash_before = sha256(BASE_FILE)
if not LEVELS.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"Could not derive {MAP} from {BASE}")

actors = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
mesh_swaps = []
for family, labels in {
    "MR01": ("LB-DOCK-MR01-01", "LB-DOCK-MR01-02"),
    "CR01": ("LB-DOCK-CR01-01", "LB-DOCK-CR01-02"),
}.items():
    mesh = LIB.load_asset(RESOLVED[family])
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing clean resolved dock mesh {RESOLVED[family]}")
    for label in labels:
        actor = actors.get(label)
        if not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError(f"Missing dock visual {label}")
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
        actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
        actor.tags = list(actor.tags) + [unreal.Name("LB.Dock.Mesh.ResolvedMaterials.v006")]
        mesh_swaps.append({"actor": label, "mesh": mesh.get_path_name()})

camera_rows = []
for name, spec in CAMERAS.items():
    camera = actors.get(spec["old"])
    if not isinstance(camera, unreal.CameraActor):
        raise RuntimeError(f"Missing inherited camera {spec['old']}")
    location = unreal.Vector(*spec["location"])
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(*spec["target"])), False)
    camera.set_actor_label(spec["new"])
    camera.camera_component.set_editor_property("field_of_view", spec["fov"])
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.35,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera_rows.append({"name": name, "actor": spec["new"], "location_cm": list(spec["location"]), "target_cm": list(spec["target"]), "fov": spec["fov"]})

lights = []
for suffix, x, y in LIGHT_ROOTS:
    location = unreal.Vector(x, y - 430.0, 440.0)
    light = ACTORS.spawn_actor_from_class(unreal.RectLight, location, unreal.Rotator())
    if light is None:
        raise RuntimeError(f"Could not spawn dock task light {suffix}")
    label = f"LB_SUPPORT_DOCK_TASK_LIGHT_{suffix}_v256"
    light.set_actor_label(label)
    light.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(x, y, 65.0)), False)
    light.rect_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.rect_light_component.set_editor_properties({
        "intensity": 1200.0,
        "attenuation_radius": 900.0,
        "source_width": 320.0,
        "source_height": 160.0,
        "light_color": unreal.Color(210, 225, 230, 255),
        "cast_shadows": False,
    })
    light.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Lighting.IndustrialLED.Task"),
        unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
        unreal.Name("LB.SupportRobot.DockTaskLight"),
    ]
    lights.append(label)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not LEVELS.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
base_hash_after = sha256(BASE_FILE)
if base_hash_before != base_hash_after:
    raise RuntimeError("Protected v255 changed while building v256")

payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-visual-build-v256/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CLEAN_DOCK_MESHES_USEFUL_FIXED_CAMERAS_AND_RESTRAINED_TASK_LIGHTING__FRESH_VISUAL_COLLISION_NAV_RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE),
    "resolved_dock_meshes": mesh_swaps,
    "cameras": camera_rows,
    "task_lights": lights,
    "task_light_intensity": 1200.0,
    "camera_exposure_bias": 0.35,
    "lighting_authority": "preview task lighting only; no lux claim",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_SUPPORT_FLEET_VISUAL_V256_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
