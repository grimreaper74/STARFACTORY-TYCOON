"""Build a camera-corrected visual successor directly from protected fleet v255.

The v257 pair cameras looked between berths separated by 12--14 metres and
therefore cropped the actual docked robots.  v258 keeps the validated berth
geometry and authority unchanged, swaps only to resolved-material meshes, and
adds one fixed evidence camera per berth plus a restrained overview.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v258"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v258.umap"
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_visual_build_v258.json"

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LIB = unreal.EditorAssetLibrary

RESOLVED = {
    "MR01": "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_MR01_ServiceDock_ResolvedMaterials_v006",
    "CR01": "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_CR01_ServiceDock_ResolvedMaterials_v006",
}
BERTHS = (
    ("mr01_01", "MR01", -6495.0, 5160.0, 75.0),
    ("mr01_02", "MR01", -5095.0, 5160.0, 75.0),
    ("cr01_01", "CR01", -1495.0, 5160.0, 70.0),
    ("cr01_02", "CR01", -295.0, 5160.0, 70.0),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def add_camera(label, location, target, fov):
    position = unreal.Vector(*location)
    camera = ACTORS.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    if camera is None:
        raise RuntimeError(f"Could not spawn {label}")
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -0.45,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Camera.Fixed.SupportFleet.v258"),
        unreal.Name("LB.Camera.VisualEvidence.SingleBerth"),
    ]
    return camera


if LIB.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {MAP}")
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
        raise RuntimeError(f"Missing resolved dock mesh {RESOLVED[family]}")
    for label in labels:
        dock = actors.get(label)
        if not isinstance(dock, unreal.StaticMeshActor):
            raise RuntimeError(f"Missing inherited dock {label}")
        dock.static_mesh_component.set_static_mesh(mesh)
        dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        dock.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
        dock.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
        dock.tags = list(dock.tags) + [unreal.Name("LB.Dock.Mesh.ResolvedMaterials.v006")]
        mesh_swaps.append({"actor": label, "mesh": mesh.get_path_name()})

# Remove inherited three midpoint cameras.  Their transforms are evidence of the
# rejected v255 framing and are not suitable authorities for a two-berth span.
removed_cameras = []
for label in (
    "LB_SUPPORT_FLEET_CAM_MR01_v255",
    "LB_SUPPORT_FLEET_CAM_CR01_v255",
    "LB_SUPPORT_FLEET_CAM_OVERVIEW_v255",
):
    actor = actors.get(label)
    if actor is not None:
        removed_cameras.append(label)
        ACTORS.destroy_actor(actor)

cameras = []
for view_id, _family, x, y, target_z in BERTHS:
    label = f"LB_SUPPORT_FLEET_CAM_{view_id.upper()}_v258"
    camera = add_camera(label, (x, y - 760.0, 235.0), (x, y + 20.0, target_z), 54.0)
    cameras.append({"view": view_id, "actor": label})

overview = add_camera(
    "LB_SUPPORT_FLEET_CAM_OVERVIEW_v258",
    (-3300.0, 3500.0, 1120.0),
    (-3300.0, 5160.0, 45.0),
    88.0,
)
cameras.append({"view": "overview", "actor": overview.get_actor_label()})

lights = []
for view_id, _family, x, y, _target_z in BERTHS:
    location = unreal.Vector(x, y - 320.0, 390.0)
    light = ACTORS.spawn_actor_from_class(unreal.RectLight, location, unreal.Rotator())
    if light is None:
        raise RuntimeError(f"Could not spawn task light {view_id}")
    label = f"LB_SUPPORT_DOCK_TASK_LIGHT_{view_id.upper()}_v258"
    light.set_actor_label(label)
    light.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(x, y, 65.0)), False)
    light.rect_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.rect_light_component.set_editor_properties({
        "intensity": 325.0,
        "attenuation_radius": 700.0,
        "source_width": 240.0,
        "source_height": 120.0,
        "light_color": unreal.Color(205, 220, 228, 255),
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
    raise RuntimeError("Protected v255 changed while building v258")

payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-visual-build-v258/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ONE_FIXED_CAMERA_PER_BERTH_AND_RESTRAINED_OVERVIEW__FRESH_VISUAL_COLLISION_NAV_RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE),
    "resolved_dock_meshes": mesh_swaps,
    "removed_rejected_midpoint_cameras": removed_cameras,
    "cameras": cameras,
    "task_lights": lights,
    "task_light_intensity": 325.0,
    "camera_exposure_bias": -0.45,
    "geometry_or_authority_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_SUPPORT_FLEET_VISUAL_V258_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
