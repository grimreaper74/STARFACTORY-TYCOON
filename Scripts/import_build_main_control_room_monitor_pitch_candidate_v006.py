"""Import the v005 12-degree monitor source into an isolated Unreal v006 map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/ControlRoom/MainControlRoom_v005/fbx_candidate"
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedCompositionCandidate_v004"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_MonitorPitchCandidate_v006"
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v006"
MAT = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_monitor_pitch_import_build_v006.json"

IMPORTS = {
    "Interaction": "CA_MW_MCR_Interaction_v005_CANDIDATE.fbx",
    "State_Mothballed": "CA_MW_MCR_State_Mothballed_v005_CANDIDATE.fbx",
}

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
missing = [str(SOURCE / filename) for filename in IMPORTS.values() if not (SOURCE / filename).is_file()]
if missing:
    raise RuntimeError(f"missing corrected v005 FBX sources: {missing}")

tasks = []
asset_paths = {}
for category, filename in IMPORTS.items():
    destination_name = f"SM_CA_MW_MCR_{category}_v006"
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
        "import_materials": False,
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
material_bindings = {}
for category, asset_path in asset_paths.items():
    mesh = library.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing imported mesh: {asset_path}")
        continue
    bound = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material = library.load_asset(f"{MAT}/{slot_name}_v002")
        if not isinstance(material, unreal.MaterialInterface):
            failures.append(f"missing v002 semantic material for slot {slot_name}")
            continue
        mesh.set_material(index, material)
        bound.append(slot_name)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    meshes[category] = mesh
    material_bindings[category] = bound

if failures:
    raise RuntimeError("; ".join(failures))
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
for category, mesh in meshes.items():
    actor = actors.get(f"LB_MCR_V004_{category}")
    if actor is None:
        failures.append(f"missing v004 map actor: {category}")
        continue
    actor.static_mesh_component.set_editor_property("static_mesh", mesh)
    actor.set_actor_label(f"LB_MCR_V006_{category}")
    actor.tags = [unreal.Name("LB.ControlRoom.v006"), unreal.Name(f"LB.ControlRoom.Category.{category}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

camera_names = ("SeatedPlayer", "Front", "Elevated", "SystemsWall")
for name in camera_names:
    actor = actors.get(f"LB_MCR_V004_CAM_{name}")
    if actor is None:
        failures.append(f"missing v004 camera: {name}")
        continue
    actor.set_actor_label(f"LB_MCR_V006_CAM_{name}")
    if name == "Elevated":
        location = unreal.Vector(500, 300, 290)
        target = unreal.Vector(0, -55, 120)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        actor.camera_component.set_editor_property("field_of_view", 76.0)
    actor.tags = [unreal.Name("LB.ControlRoom.v006"), unreal.Name(f"LB.ControlRoom.Camera.{name}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_MCR_V004_"):
        actor.set_actor_label(label.replace("V004", "V006"))
    if any(str(tag) == "LB.ControlRoom.v004" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v006" if str(tag) == "LB.ControlRoom.v004" else str(tag)) for tag in actor.tags]

levels.save_current_level()
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "cairnwell/audit/main-control-room-monitor-pitch-import-build-v006/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TWELVE_DEGREE_CONSOLE_MONITOR_SOURCE_IMPORTED__FIXED_CAMERA_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V006_IMPORT_BUILD__NOT_PROMOTED",
    "source_package": "SourceAssets/ControlRoom/MainControlRoom_v005",
    "source_map": BASE,
    "map": MAP,
    "corrected_source_pitch_degrees": 12.0,
    "authoritative_range_degrees": [10.0, 15.0],
    "replaced_categories": sorted(meshes.keys()),
    "material_bindings": material_bindings,
    "promotion_authorized": False,
    "gameplay_wired": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

