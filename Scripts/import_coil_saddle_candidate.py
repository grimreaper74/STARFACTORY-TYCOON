"""Import the reusable padded coil-saddle candidate with controlled materials."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/IndustrialKit/CoilSaddle/SM_LB_CoilSaddle_Candidate_v001.fbx"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilSaddle"
NAME = "SM_LB_CoilSaddle_Candidate_v001"
AUDIT = ROOT / "Saved/Audits/coil_saddle_candidate_v001.json"

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE), "destination_path": DEST, "destination_name": NAME,
    "automated": True, "replace_existing": True, "replace_existing_settings": True, "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True, "import_as_skeletal": False,
    "import_materials": False, "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
data = options.get_editor_property("static_mesh_import_data")
data.set_editor_properties({
    "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
    "force_front_x_axis": False, "generate_lightmap_u_vs": True,
    "auto_generate_collision": True, "remove_degenerates": True,
})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = unreal.load_asset(f"{DEST}/{NAME}")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Coil saddle did not import as a StaticMesh")

paths = {
    "blue": "/Game/LineBoss/Materials/M_LB_Zone_PRESS_RECEIVING.M_LB_Zone_PRESS_RECEIVING",
    "edge": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
    "rubber": "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber.M_PR005_Rubber",
    "yellow": "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow",
}
mats = {key: unreal.load_asset(value) for key, value in paths.items()}
if any(value is None for value in mats.values()):
    raise RuntimeError(f"Missing controlled saddle materials: {mats}")

assignments = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
    low = name.lower()
    selected = mats["yellow"] if "yellow" in low else mats["rubber"] if "rubber" in low else mats["edge"] if ("edge" in low or "fastener" in low) else mats["blue"]
    mesh.set_material(index, selected)
    assignments.append({"slot": name, "material": selected.get_path_name()})
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

box = mesh.get_bounding_box()
result = {
    "status": "CANDIDATE_NOT_PROMOTED",
    "asset": mesh.get_path_name(),
    "rated_coil_mass_kg": 30000,
    "bounds_cm": {
        "min": list(box.min.to_tuple()), "max": list(box.max.to_tuple()),
        "size": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
    },
    "materials": assignments,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_COIL_SADDLE_IMPORT_PASS asset={result['asset']}")
