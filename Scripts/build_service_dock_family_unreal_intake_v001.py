"""Import MR01/CR01 closed dock meshes into a fresh isolated Unreal intake map."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyIntake_v003"
DEST_MR = "/Game/LineBoss/SupportRobots/ServiceDocks/Intake_v001/MR01"
DEST_CR = "/Game/LineBoss/SupportRobots/ServiceDocks/Intake_v001/CR01"
MR_NAME = "SM_LB_MR01_ServiceDock_ClosedIntake_v002"
CR_NAME = "SM_LB_CR01_ServiceDock_ClosedIntake_v002"
PROJECT = Path(unreal.Paths.project_dir())
MR_FBX = PROJECT / "SourceAssets/SharedSystems/MaintenanceAMR/Dock_Candidate_v005/UnrealIntake_v002" / f"{MR_NAME}.fbx"
CR_FBX = PROJECT / "SourceAssets/SharedSystems/CleaningAMR/Dock_Candidate_v008/UnrealIntake_v002" / f"{CR_NAME}.fbx"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/service_dock_family_unreal_intake_build_v003.json"
V253 = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def import_mesh(fbx: Path, destination: str, name: str):
    if not fbx.is_file():
        raise RuntimeError(f"Missing export {fbx}")
    asset_path = f"{destination}/{name}"
    if lib.does_asset_exist(asset_path):
        mesh = lib.load_asset(asset_path)
        if mesh is None:
            raise RuntimeError(f"Existing intake asset could not be loaded: {asset_path}")
        return asset_path, mesh
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(fbx), "destination_path": destination, "destination_name": name,
        "automated": True, "replace_existing": False, "replace_existing_settings": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": True, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": True, "remove_degenerates": True,
    })
    task.options = options
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset(asset_path)
    if mesh is None:
        raise RuntimeError(f"Import failed: {asset_path}; returned {task.imported_object_paths}")
    lib.save_loaded_asset(mesh, only_if_is_dirty=False)
    return asset_path, mesh


def vec(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


def spawn_mesh(label, mesh, location):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.ServiceDockIntake.v001"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Runtime.Authority.NotYetBound")]
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    comp.set_collision_profile_name(unreal.Name("BlockAll"))
    comp.set_editor_property("can_ever_affect_navigation", True)
    return actor


def add_camera(label, location, target, fov=45.0):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.ServiceDockIntake.v001")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


v253_before = sha256(V253)
if lib.does_asset_exist(MAP):
    raise RuntimeError(f"Fresh isolated intake map already exists: {MAP}")
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
mr_path, mr_mesh = import_mesh(MR_FBX, DEST_MR, MR_NAME)
cr_path, cr_mesh = import_mesh(CR_FBX, DEST_CR, CR_NAME)

mr_size = mr_mesh.get_bounds().box_extent * 2.0
cr_size = cr_mesh.get_bounds().box_extent * 2.0
failures = []
if not (259.0 <= mr_size.x <= 261.0 and 154.0 <= mr_size.y <= 156.0 and 170.0 <= mr_size.z <= 171.5):
    failures.append(f"MR imported bounds unexpected: {vec(mr_size)}")
if not (259.0 <= cr_size.x <= 261.0 and 148.0 <= cr_size.y <= 150.0 and 170.0 <= cr_size.z <= 171.5):
    failures.append(f"CR imported bounds unexpected: {vec(cr_size)}")
if failures:
    raise RuntimeError("; ".join(failures))

if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create {MAP}")
cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
if cube is None:
    raise RuntimeError("Missing engine cube")
floor = spawn_mesh("LB_DOCK_INTAKE_Floor", cube, (0.0, 0.0, -10.0))
floor.set_actor_scale3d(unreal.Vector(10.0, 8.0, 0.2))
floor.tags = [unreal.Name("LB.Asset.Candidate.ServiceDockIntake.v001"), unreal.Name("LB.Validation.SealedConcreteStage")]

mr_actor = spawn_mesh("LB_DOCK_INTAKE_MR01_v005", mr_mesh, (0.0, -230.0, 0.0))
cr_actor = spawn_mesh("LB_DOCK_INTAKE_CR01_v008", cr_mesh, (0.0, 230.0, 0.0))
mr_actor.tags = [unreal.Name("LB.Asset.Candidate.ServiceDockIntake.v002"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Runtime.Authority.NotYetBound"), unreal.Name("LB.Dock.Type.MR01"), unreal.Name("LB.Dock.FleetInstancesRequired.2")]
cr_actor.tags = [unreal.Name("LB.Asset.Candidate.ServiceDockIntake.v002"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Runtime.Authority.NotYetBound"), unreal.Name("LB.Dock.Type.CR01"), unreal.Name("LB.Dock.FleetInstancesRequired.2")]

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 300.0), unreal.Rotator())
sky.set_actor_label("LB_DOCK_INTAKE_Sky")
sky.light_component.set_editor_property("intensity", 1.0)
for index, (location, intensity, colour) in enumerate((
    ((-300.0, -350.0, 430.0), 3200.0, unreal.Color(209, 230, 255, 255)),
    ((260.0, 330.0, 360.0), 2600.0, unreal.Color(255, 199, 140, 255)),
), start=1):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator(pitch=-55.0, yaw=35.0 if index == 1 else -145.0))
    light.set_actor_label(f"LB_DOCK_INTAKE_Rect_{index:02d}")
    light.light_component.set_editor_properties({"intensity": intensity, "source_width": 260.0, "source_height": 180.0, "light_color": colour})

cameras = [
    add_camera("LB_DOCK_INTAKE_CAM_Family", (-620.0, -520.0, 330.0), (0.0, 0.0, 80.0), 48.0),
    add_camera("LB_DOCK_INTAKE_CAM_MR01", (-430.0, -520.0, 250.0), (0.0, -230.0, 80.0), 42.0),
    add_camera("LB_DOCK_INTAKE_CAM_CR01", (-430.0, 520.0, 250.0), (0.0, 230.0, 80.0), 42.0),
]
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

map_file = PROJECT / "Content/LineBoss/Developer/Validation/LB_ServiceDockFamilyIntake_v003.umap"
mr_file = PROJECT / "Content/LineBoss/SupportRobots/ServiceDocks/Intake_v001/MR01" / f"{MR_NAME}.uasset"
cr_file = PROJECT / "Content/LineBoss/SupportRobots/ServiceDocks/Intake_v001/CR01" / f"{CR_NAME}.uasset"
v253_after = sha256(V253)
if v253_before != v253_after:
    raise RuntimeError("Protected v253 changed during isolated intake")
for path in (map_file, mr_file, cr_file):
    if not path.is_file():
        raise RuntimeError(f"Expected saved package missing: {path}")

payload = {
    "$schema": "cairnwell/audit/service-dock-family-unreal-intake-build-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_ISOLATED_CLOSED_DOCK_UNREAL_INTAKE__VISUAL_COLLISION_RUNTIME_GATES_OPEN__NOT_PROMOTED",
    "map": MAP,
    "map_sha256": sha256(map_file),
    "assets": {
        "mr01": {"path": mr_path, "uasset_sha256": sha256(mr_file), "bounds_cm": vec(mr_size), "source_fbx_sha256": sha256(MR_FBX)},
        "cr01": {"path": cr_path, "uasset_sha256": sha256(cr_file), "bounds_cm": vec(cr_size), "source_fbx_sha256": sha256(CR_FBX)},
    },
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "collision_profile": "BlockAll with FBX auto-generated collision; exact collision audit still required",
    "v253_sha256_before": v253_before,
    "v253_sha256_after": v253_after,
    "holds": ["Closed-state intake only", "No support robot actor fit yet", "No moving service components or runtime", "No Press Shop placement"],
    "failures": failures,
    "promotion_authorized": False,
  }
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_FAMILY_INTAKE_V003_PASS")
unreal.log(json.dumps(payload, indent=2))
