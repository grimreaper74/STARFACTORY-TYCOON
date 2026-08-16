"""Import and audit reusable Press Shop front-end dressing modules."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/IndustrialKit/FrontEndDressing"
DEST = "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing"
AUDIT = ROOT / "Saved/Audits/front_end_dressing_kit_candidate_v001.json"
NAMES = [
    "SM_LB_ServiceCabinet_1800_v001",
    "SM_LB_FloorTrenchGrate_1000_v001",
    "SM_LB_SafetyBollard_1000_v001",
    "SM_LB_InspectionMast_3000_v001",
    "SM_LB_PackagingPrepBench_2400_v001",
    "SM_LB_PackagingRecoveryBin_v001",
    "SM_LB_EStopPedestal_1300_v001",
]


tasks = []
for name in NAMES:
    source = SOURCE / f"{name}.fbx"
    if not source.exists():
        raise RuntimeError(f"Missing front-end dressing source {source}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": DEST,
        "destination_name": name,
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
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
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": True,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material_paths = {
    "yellow": "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow",
    "charcoal": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
    "painted": "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal",
    "stainless": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_SS304.M_HMI04_SS304",
    "rubber": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_Rubber.M_HMI04_Rubber",
    "red": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_Red.M_HMI04_Red",
    "green": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_Green.M_HMI04_Green",
    "amber": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_Amber.M_HMI04_Amber",
    "blue": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_Blue.M_HMI04_Blue",
    "white": "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/M_HMI04_White.M_HMI04_White",
}
mats = {key: unreal.load_asset(path) for key, path in material_paths.items()}
missing_mats = [key for key, value in mats.items() if value is None]
if missing_mats:
    raise RuntimeError(f"Missing controlled front-end materials: {missing_mats}")


def select_material(slot_name: str):
    low = slot_name.lower()
    for key in ("yellow", "charcoal", "painted", "stainless", "rubber", "red", "green", "amber", "blue", "white"):
        if key in low:
            return mats[key]
    return mats["painted"]


records = []
for name in NAMES:
    mesh = unreal.load_asset(f"{DEST}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported dressing module {name}")
    if unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh) == 0:
        unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
    assignments = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(
            slot.get_editor_property("imported_material_slot_name")
            or slot.get_editor_property("material_slot_name")
        )
        selected = select_material(slot_name)
        mesh.set_material(index, selected)
        assignments.append({"slot": slot_name, "material": selected.get_path_name()})
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    bounds = mesh.get_bounding_box()
    records.append({
        "asset": mesh.get_path_name(),
        "bounds_cm": {
            "min": list(bounds.min.to_tuple()),
            "max": list(bounds.max.to_tuple()),
            "size": [
                bounds.max.x - bounds.min.x,
                bounds.max.y - bounds.min.y,
                bounds.max.z - bounds.min.z,
            ],
        },
        "material_assignments": assignments,
        "simple_collision_count": unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh),
    })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "CANDIDATE_NOT_PROMOTED",
    "source_blend": str(SOURCE / "LB_FrontEndDressingKit_Candidate_v001.blend"),
    "destination": DEST,
    "module_count": len(records),
    "records": records,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_FRONT_END_DRESSING_IMPORT_PASS modules={len(records)} audit={AUDIT}")
