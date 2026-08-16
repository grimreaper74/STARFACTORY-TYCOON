"""Build a fresh isolated visual/runtime validation stage for modular docks."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v026"
PROJECT = Path(unreal.Paths.project_dir())
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/service_dock_modular_runtime_validation_build_v026.json"
PROTECTED = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269.umap"

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
if not levels.new_level(MAP):
    raise RuntimeError(f"failed to create {MAP}")

cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -10), unreal.Rotator())
floor.set_actor_label("LB_DOCK_V026_SealedConcreteStage")
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(12, 8, 0.2))
floor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))

dock_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBSupportRobotServiceDock")
if not dock_class:
    raise RuntimeError("native service dock class did not load")
mr = actors.spawn_actor_from_class(dock_class, unreal.Vector(0, -240, 0), unreal.Rotator(yaw=180))
cr = actors.spawn_actor_from_class(dock_class, unreal.Vector(0, 240, 0), unreal.Rotator(yaw=180))
mr.set_actor_label("LB_DOCK_V026_MR01_RUNTIME")
cr.set_actor_label("LB_DOCK_V026_CR01_RUNTIME")
if not mr.configure_dock("LB-DOCK-MR01-V026", unreal.LBServiceDockVariant.MR01_MAINTENANCE):
    raise RuntimeError("MR01 dock configure failed")
if not cr.configure_dock("LB-DOCK-CR01-V026", unreal.LBServiceDockVariant.CR01_CLEANING):
    raise RuntimeError("CR01 dock configure failed")
mr.tags = [unreal.Name("LB.Asset.Candidate.ServiceDock.Runtime.v026"), unreal.Name("LB.Asset.CandidateNotPromoted")]
cr.tags = list(mr.tags)

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 400), unreal.Rotator())
sky.set_actor_label("LB_DOCK_V026_Sky")
sky.light_component.set_editor_property("intensity", 0.8)
for index, (location, intensity, colour) in enumerate((
    ((-320, -420, 420), 2200, unreal.Color(210, 230, 255, 255)),
    ((300, 420, 350), 1800, unreal.Color(255, 205, 155, 255)),
), 1):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator(pitch=-55, yaw=35 if index == 1 else -145))
    light.set_actor_label(f"LB_DOCK_V026_Key_{index:02d}")
    light.light_component.set_editor_properties({"intensity": intensity, "source_width": 260.0, "source_height": 180.0, "light_color": colour})

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-680, -540, 310), unreal.Rotator())
camera.set_actor_label("LB_DOCK_V026_CAM_FAMILY")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 80)), False)
camera.camera_component.set_editor_properties({"field_of_view": 46.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})

if not levels.save_current_level():
    raise RuntimeError("failed to save isolated validation map")
map_file = PROJECT / "Content/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v026.umap"
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("protected v269 changed during isolated validation build")

payload = {
    "$schema": "cairnwell/audit/service-dock-modular-runtime-validation-build-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_ISOLATED_RUNTIME_DOCK_STAGE__VISUAL_AND_MAP_INTEGRATION_GATES_OPEN__NOT_PROMOTED",
    "map": MAP,
    "map_sha256": sha256(map_file),
    "actors": [mr.get_actor_label(), cr.get_actor_label()],
    "camera": camera.get_actor_label(),
    "protected_v269_sha256_before": protected_before,
    "protected_v269_sha256_after": protected_after,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_MODULAR_RUNTIME_VALIDATION_V026_PASS")
