"""Import the custom safety-barrier candidates and bind controlled materials."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/IndustrialKit/SafetyBarrier"
DEST = "/Game/LineBoss/IndustrialKit/Safety/Barrier"
AUDIT = ROOT / "Saved/Audits/safety_barrier_kit_candidate_v001.json"
NAMES = [
    "SM_LB_GuardPanel_2000_v001",
    "SM_LB_GuardPost_1500_v001",
    "SM_LB_InterlockedGate_1200_v001",
    "SM_LB_GuardInterlockBox_v001",
]

tasks = []
for name in NAMES:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / f"{name}.fbx"),
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
    "dark": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
    "steel": (
        "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
        "M_HMI04_SS304.M_HMI04_SS304"
    ),
    "red": (
        "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
        "M_HMI04_Red.M_HMI04_Red"
    ),
    "green": (
        "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
        "M_HMI04_Green.M_HMI04_Green"
    ),
}
mats = {key: unreal.load_asset(path) for key, path in material_paths.items()}
if any(value is None for value in mats.values()):
    raise RuntimeError(f"Missing controlled barrier materials: {mats}")

records = []
for name in NAMES:
    mesh = unreal.load_asset(f"{DEST}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported safety-barrier module {name}")
    if unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh) == 0:
        unreal.EditorStaticMeshLibrary.add_simple_collisions(
            mesh, unreal.ScriptingCollisionShapeType.BOX,
        )
    assignments = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(
            slot.get_editor_property("imported_material_slot_name")
            or slot.get_editor_property("material_slot_name")
        )
        low = slot_name.lower()
        selected = mats["yellow"]
        if "dark" in low or "wire" in low:
            selected = mats["dark"]
        elif "galvanized" in low or "fastener" in low or "steel" in low:
            selected = mats["steel"]
        elif "red" in low:
            selected = mats["red"]
        elif "green" in low:
            selected = mats["green"]
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
    "reason": "Replaces vendor fence rejected by fixed-camera visual review",
    "module_count": len(records),
    "animation_contract": {
        "gate_asset": "SM_LB_InterlockedGate_1200_v001",
        "pivot": "hinge at local origin",
        "state_roles": ["closed_locked", "opening", "open_safe_access", "closing", "fault"],
    },
    "records": records,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_SAFETY_BARRIER_IMPORT_PASS modules={len(records)}")
