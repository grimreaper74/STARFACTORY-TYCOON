"""Import modular bridge-crane candidates and bind controlled materials."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/IndustrialKit/BridgeCrane"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane"
AUDIT = ROOT / "Saved/Audits/bridge_crane_kit_candidate_v001.json"
NAMES = [
    "SM_LB_Crane_BridgeGirder_4500_v001",
    "SM_LB_Crane_EndTruck_v001",
    "SM_LB_Crane_Trolley_v001",
    "SM_LB_Crane_HoistBlock_v001",
    "SM_LB_Crane_CHook_v001",
    "SM_LB_Crane_RunwayBeam_3000_v001",
    "SM_LB_Crane_Column_14300_v001",
]

tasks = []
for name in NAMES:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / f"{name}.fbx"), "destination_path": DEST,
        "destination_name": name, "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True,
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
    tasks.append(task)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material_paths = {
    "yellow": "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow",
    "dark": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
    "steel": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_SS304.M_HMI04_SS304",
    "rubber": "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber.M_PR005_Rubber",
    "red": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_Red.M_HMI04_Red",
}
mats = {key: unreal.load_asset(path) for key, path in material_paths.items()}
if any(value is None for value in mats.values()):
    raise RuntimeError(f"Missing controlled crane materials: {mats}")

records = []
for name in NAMES:
    mesh = unreal.load_asset(f"{DEST}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported crane module {name}")
    assignments = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        low = slot_name.lower()
        selected = mats["yellow"]
        if "dark" in low:
            selected = mats["dark"]
        elif "exposed" in low or "fastener" in low:
            selected = mats["steel"]
        elif "rubber" in low:
            selected = mats["rubber"]
        elif "red" in low:
            selected = mats["red"]
        mesh.set_material(index, selected)
        assignments.append({"slot": slot_name, "material": selected.get_path_name()})
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    bounds = mesh.get_bounding_box()
    records.append({
        "asset": mesh.get_path_name(),
        "bounds_cm": {
            "min": list(bounds.min.to_tuple()), "max": list(bounds.max.to_tuple()),
            "size": [bounds.max.x-bounds.min.x, bounds.max.y-bounds.min.y, bounds.max.z-bounds.min.z],
        },
        "materials": assignments,
    })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "CANDIDATE_NOT_PROMOTED", "module_count": len(records), "records": records,
    "animation_contract": ["bridge", "end_truck", "trolley", "hoist_block", "c_hook"],
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_BRIDGE_CRANE_IMPORT_PASS modules={len(records)}")
