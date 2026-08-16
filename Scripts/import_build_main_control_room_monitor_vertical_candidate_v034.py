"""Import the corrected 12-degrees-back-from-vertical control-room monitors."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/ControlRoom/MainControlRoom_v034/fbx_candidate"
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVFocusCandidate_v033"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_MonitorVerticalCandidate_v034"
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v034"
MAT = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_monitor_vertical_build_v034.json"
IMPORTS = {
    "Interaction": "CA_MW_MCR_Interaction_v034_CANDIDATE.fbx",
    "State_Mothballed": "CA_MW_MCR_State_Mothballed_v034_CANDIDATE.fbx",
}

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
missing = [str(SOURCE / name) for name in IMPORTS.values() if not (SOURCE / name).is_file()]
if missing:
    raise RuntimeError(f"missing corrected monitor FBX sources: {missing}")

tasks = []
asset_paths = {}
for category, filename in IMPORTS.items():
    destination_name = f"SM_CA_MW_MCR_{category}_v034"
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
            failures.append(f"missing semantic material for slot {slot_name}")
            continue
        mesh.set_material(index, material)
        bound.append(slot_name)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    meshes[category] = mesh
    material_bindings[category] = bound

if failures:
    raise RuntimeError("; ".join(failures))
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

replaced = {}
for category, mesh in meshes.items():
    category_tag = f"LB.ControlRoom.Category.{category}"
    matches = [
        actor for actor in actors_api.get_all_level_actors()
        if any(str(tag) == category_tag for tag in actor.tags)
        and isinstance(actor, unreal.StaticMeshActor)
    ]
    if len(matches) != 1:
        failures.append(f"expected one {category_tag} actor, found {len(matches)}")
        continue
    actor = matches[0]
    old_label = actor.get_actor_label()
    actor.static_mesh_component.set_editor_property("static_mesh", mesh)
    actor.set_actor_label(f"LB_MCR_V034_{category}")
    actor.tags = [
        unreal.Name("LB.ControlRoom.v034" if str(tag).startswith("LB.ControlRoom.v0") else str(tag))
        for tag in actor.tags
    ]
    if not any(str(tag) == "LB.Asset.CandidateNotPromoted" for tag in actor.tags):
        actor.tags = list(actor.tags) + [unreal.Name("LB.Asset.CandidateNotPromoted")]
    replaced[category] = {"old_label": old_label, "new_label": actor.get_actor_label()}

if failures:
    raise RuntimeError("; ".join(failures))

levels.save_current_level()
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "cairnwell/audit/main-control-room-monitor-vertical-build-v034/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__MONITORS_12_DEGREES_BACK_FROM_VERTICAL__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_package": "SourceAssets/ControlRoom/MainControlRoom_v034",
    "source_map": BASE,
    "map": MAP,
    "source_rotation_degrees_from_horizontal": 78.0,
    "operator_tilt_degrees_back_from_vertical": 12.0,
    "corrected_basis": "Blender mesh X rotation is measured from horizontal; 90 - 12 = 78 degrees",
    "replaced": replaced,
    "material_bindings": material_bindings,
    "real_pr004_cctv_and_seated_gameplay_preserved": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))
