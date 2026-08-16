"""Import downward operator-aimed monitor meshes into playable v007 as v008."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/ControlRoom/MainControlRoom_v006/fbx_candidate"
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PlayableCandidate_v007"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008"
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v008"
MAT = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_operator_aim_import_build_v008.json"
IMPORTS = {
    "Interaction": "CA_MW_MCR_Interaction_v006_CANDIDATE.fbx",
    "State_Mothballed": "CA_MW_MCR_State_Mothballed_v006_CANDIDATE.fbx",
}

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
missing = [str(SOURCE / name) for name in IMPORTS.values() if not (SOURCE / name).is_file()]
if missing:
    raise RuntimeError(f"missing v006 operator-aim FBX sources: {missing}")

tasks = []
asset_paths = {}
for category, filename in IMPORTS.items():
    destination_name = f"SM_CA_MW_MCR_{category}_v008"
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

asset_tools.import_asset_tasks(tasks)
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
    actor = actors.get(f"LB_MCR_V006_{category}")
    if actor is None:
        failures.append(f"missing inherited v006 map actor: {category}")
        continue
    actor.static_mesh_component.set_editor_property("static_mesh", mesh)
    actor.set_actor_label(f"LB_MCR_V008_{category}")
    actor.tags = [unreal.Name("LB.ControlRoom.v008"), unreal.Name(f"LB.ControlRoom.Category.{category}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_MCR_V006_CAM_"):
        actor.set_actor_label(label.replace("V006", "V008"))
    if any(str(tag) == "LB.ControlRoom.v007" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v008" if str(tag) == "LB.ControlRoom.v007" else str(tag)) for tag in actor.tags]

levels.save_current_level()
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "cairnwell/audit/main-control-room-operator-aim-import-build-v008/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__MONITORS_AIMED_DOWN_TOWARD_SEATED_OPERATOR__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V008_OPERATOR_AIM_BUILD__NOT_PROMOTED",
    "source_package": "SourceAssets/ControlRoom/MainControlRoom_v006",
    "source_map": BASE,
    "map": MAP,
    "source_pitch_degrees": -12.0,
    "pitch_basis": "Blender negative-X aims monitor normals down toward the seated 1.12 m operator eye point",
    "replaced_categories": sorted(meshes.keys()),
    "material_bindings": material_bindings,
    "seated_game_mode_preserved": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
