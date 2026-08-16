"""Build a fresh corrected isolated stage; never duplicate/load an open UWorld."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import unreal

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VERSION = int(args[0]) if args else 29
TAG = f"V{VERSION:03d}"
MAP = f"/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v{VERSION:03d}"
PROJECT = Path(unreal.Paths.project_dir()).resolve()
AUDIT = Path(unreal.Paths.project_saved_dir()).resolve() / f"Audits/SupportRobots/service_dock_modular_runtime_validation_build_v{VERSION:03d}.json"
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
floor.set_actor_label(f"LB_DOCK_{TAG}_SealedConcreteStage")
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(12, 8, 0.2))
floor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))

dock_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBSupportRobotServiceDock")
if not dock_class:
    raise RuntimeError("native service dock class did not load")
mr = actors.spawn_actor_from_class(dock_class, unreal.Vector(0, -240, 0), unreal.Rotator(yaw=180))
cr = actors.spawn_actor_from_class(dock_class, unreal.Vector(0, 240, 0), unreal.Rotator(yaw=180))
mr.set_actor_label(f"LB_DOCK_{TAG}_MR01_RUNTIME")
cr.set_actor_label(f"LB_DOCK_{TAG}_CR01_RUNTIME")
if not mr.configure_dock(f"LB-DOCK-MR01-{TAG}", unreal.LBServiceDockVariant.MR01_MAINTENANCE):
    raise RuntimeError("MR01 dock configure failed")
if not cr.configure_dock(f"LB-DOCK-CR01-{TAG}", unreal.LBServiceDockVariant.CR01_CLEANING):
    raise RuntimeError("CR01 dock configure failed")
tags = [unreal.Name(f"LB.Asset.Candidate.ServiceDock.Runtime.v{VERSION:03d}"), unreal.Name("LB.Asset.CandidateNotPromoted")]
mr.tags = tags
cr.tags = tags

comparison_actors = []
if VERSION >= 29:
    for label, path, location in (
        (f"LB_DOCK_{TAG}_MR01_RESOLVED_CONTROL", "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_MR01_ServiceDock_ResolvedMaterials_v006", (360, -240, 0)),
        (f"LB_DOCK_{TAG}_CR01_RESOLVED_CONTROL", "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_CR01_ServiceDock_ResolvedMaterials_v006", (360, 240, 0)),
    ):
        mesh = lib.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"resolved comparison mesh missing: {path}")
        control = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(yaw=180))
        control.set_actor_label(label)
        control.static_mesh_component.set_static_mesh(mesh)
        control.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comparison_actors.append(control)

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 400), unreal.Rotator())
sky.set_actor_label(f"LB_DOCK_{TAG}_Sky")
sky.light_component.set_editor_property("intensity", 0.35)
for index, (location, intensity, colour) in enumerate((
    ((-320, -420, 420), 700.0, unreal.Color(210, 230, 255, 255)),
    ((300, 420, 350), 450.0, unreal.Color(255, 205, 155, 255)),
), 1):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator(pitch=-55, yaw=35 if index == 1 else -145))
    light.set_actor_label(f"LB_DOCK_{TAG}_Key_{index:02d}")
    light.light_component.set_editor_properties({"intensity": intensity, "source_width": 260.0, "source_height": 180.0, "light_color": colour})

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-760, -660, 330), unreal.Rotator())
camera.set_actor_label(f"LB_DOCK_{TAG}_CAM_FAMILY")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(160 if VERSION >= 29 else 0, 0, 80)), False)
camera.camera_component.set_editor_properties({"field_of_view": 46.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label(f"LB_DOCK_{TAG}_FixedExposure")
exposure.set_editor_property("unbound", True)
settings = exposure.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": -1.0,
})
exposure.set_editor_property("settings", settings)
if not levels.save_current_level():
    raise RuntimeError("failed to save v027")

map_file = PROJECT / f"Content/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v{VERSION:03d}.umap"
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("protected v269 changed")
payload = {
    "$schema": f"cairnwell/audit/service-dock-modular-runtime-validation-build-v{VERSION:03d}/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_ALIGNMENT_MATERIAL_AND_FIXED_EXPOSURE_SUCCESSOR__VISUAL_GATE_OPEN__NOT_PROMOTED",
    "map": MAP, "map_sha256": sha256(map_file),
    "rejected_predecessor": f"/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v{VERSION - 1:03d}",
    "changes": ["corrected Blender +Y to Unreal -Y mover placement", "retained resolved materials", "fixed validation exposure", "same-light resolved aggregate comparison controls"],
    "resolved_comparison_controls": [actor.get_actor_label() for actor in comparison_actors],
    "protected_v269_sha256_before": protected_before,
    "protected_v269_sha256_after": protected_after,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_MODULAR_RUNTIME_VALIDATION_{TAG}_PASS")
