"""Import the promoted v004 control-room source and assemble an isolated UE candidate.

Source promotion is not Unreal promotion. This script creates a candidate map,
keeps all nine authored categories independently replaceable, and adds only an
initial lighting/camera rig for the first Unreal visual gate.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/ControlRoom/MainControlRoom_v004/fbx_candidate"
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v001"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_IntegrationCandidate_v001"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_import_build_v001.json"

CATEGORIES = {
    "Architecture": "CA_MW_MCR_Architecture_v004_CANDIDATE.fbx",
    "Consoles": "CA_MW_MCR_Consoles_v004_CANDIDATE.fbx",
    "Systems": "CA_MW_MCR_Systems_v004_CANDIDATE.fbx",
    "Furniture": "CA_MW_MCR_Furniture_v004_CANDIDATE.fbx",
    "Interaction": "CA_MW_MCR_Interaction_v004_CANDIDATE.fbx",
    "Service": "CA_MW_MCR_Service_v004_CANDIDATE.fbx",
    "Identity": "CA_MW_MCR_Identity_v004_CANDIDATE.fbx",
    "State_Restored": "CA_MW_MCR_State_Restored_v004_CANDIDATE.fbx",
    "State_Mothballed": "CA_MW_MCR_State_Mothballed_v004_CANDIDATE.fbx",
}

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite existing candidate map: {MAP}")
missing_source = [str(SOURCE / filename) for filename in CATEGORIES.values() if not (SOURCE / filename).is_file()]
if missing_source:
    raise RuntimeError(f"missing v004 FBX sources: {missing_source}")

tasks = []
asset_paths = {}
for category, filename in CATEGORIES.items():
    destination_name = f"SM_CA_MW_MCR_{category}_v001"
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / filename),
        "destination_path": f"{DEST}/Meshes",
        "destination_name": destination_name,
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": True,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)
    asset_paths[category] = f"{DEST}/Meshes/{destination_name}"

tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

failures = []
meshes = {}
for category, asset_path in asset_paths.items():
    mesh = library.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing imported combined mesh: {asset_path}")
    else:
        meshes[category] = mesh
if failures:
    raise RuntimeError("; ".join(failures))

if not levels.new_level(MAP):
    raise RuntimeError(f"could not create {MAP}")


def tag(actor, *values):
    actor.tags = [unreal.Name(value) for value in values]


assembly = []
for category, mesh in meshes.items():
    actor = actors_api.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(f"LB_MCR_V001_{category}")
    tag(actor, "LB.ControlRoom.v001", f"LB.ControlRoom.Category.{category}", "LB.Asset.CandidateNotPromoted")
    if category == "State_Mothballed":
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.set_actor_hidden_in_game(True)
    assembly.append(actor.get_actor_label())

# Initial restored-state lighting. These are deliberately separate from the
# imported luminaires so Unreal light intensity remains tunable and testable.
lights = []
for row, y in enumerate((-235.0, 35.0, 235.0), start=1):
    for column, x in enumerate((-570.0, -380.0, -190.0, 0.0, 190.0, 380.0, 570.0), start=1):
        light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, 345.0), unreal.Rotator(-90, 0, 0))
        light.set_actor_label(f"LB_MCR_V001_CeilingLight_{row:02d}_{column:02d}")
        component = light.get_component_by_class(unreal.RectLightComponent)
        component.set_editor_properties({
            "intensity": 850.0,
            "source_width": 110.0,
            "source_height": 18.0,
            "attenuation_radius": 520.0,
            "light_color": unreal.Color(214, 229, 226, 255),
            "cast_shadows": True,
        })
        tag(light, "LB.ControlRoom.v001", "LB.ControlRoom.Lighting.Restored", "LB.Asset.CandidateNotPromoted")
        lights.append(light.get_actor_label())

# Fixed evidence/player cameras use UE-native look-at rotations and source
# camera positions converted from millimetres to centimetres.
cameras = []
camera_specs = {
    "SeatedPlayer": (unreal.Vector(0, -38, 112), unreal.Vector(0, 330, 180), 82.0),
    "Front": (unreal.Vector(0, -315, 175), unreal.Vector(0, 90, 155), 70.0),
    "Elevated": (unreal.Vector(650, -560, 520), unreal.Vector(0, 0, 120), 58.0),
    "SystemsWall": (unreal.Vector(0, 175, 205), unreal.Vector(0, -270, 150), 70.0),
}
for name, (location, target, fov) in camera_specs.items():
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, location, rotation)
    camera.set_actor_label(f"LB_MCR_V001_CAM_{name}")
    camera.camera_component.set_editor_property("field_of_view", fov)
    tag(camera, "LB.ControlRoom.v001", f"LB.ControlRoom.Camera.{name}", "LB.Asset.CandidateNotPromoted")
    cameras.append(camera.get_actor_label())

levels.save_current_level()
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

bounds = {}
for category, actor_label in zip(meshes.keys(), assembly):
    actor = next(actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == actor_label)
    _origin, extent = actor.get_actor_bounds(False)
    bounds[category] = [round(extent.x * 2, 3), round(extent.y * 2, 3), round(extent.z * 2, 3)]

architecture = bounds.get("Architecture", [0, 0, 0])
horizontal = sorted(architecture[:2])
if not (760.0 <= horizontal[0] <= 820.0 and 1400.0 <= horizontal[1] <= 1480.0):
    failures.append(f"architecture horizontal envelope mismatch cm: {architecture}")

payload = {
    "$schema": "cairnwell/audit/main-control-room-import-build-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_UNREAL_CONTROL_ROOM_CANDIDATE_BUILT__VISUAL_RUNTIME_GAMEPLAY_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_IMPORT_BUILD__NOT_PROMOTED",
    "source_release": "SourceAssets/ControlRoom/MainControlRoom_v004/RELEASE.json",
    "map": MAP,
    "destination": DEST,
    "assembly_actors": assembly,
    "lights": lights,
    "cameras": cameras,
    "combined_mesh_bounds_cm": bounds,
    "source_promoted": True,
    "unreal_promoted": False,
    "gameplay_wired": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
