import json
from pathlib import Path
import unreal

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/Inbound/CoilHandlerAGV_v20260810/Hybrid_v999"
DEST = "/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/coil_handler_unreal_import_v999.json"
ROWS = (
    ("SM_Cairnwell_AGV_CHF01_StaticBody_v999.fbx", "SM_Cairnwell_AGV_CHF01_StaticBody_v999"),
    ("SM_Cairnwell_AGV_CHF01_LiftAssembly_v999.fbx", "SM_Cairnwell_AGV_CHF01_LiftAssembly_v999"),
)

tasks = []
for filename, name in ROWS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(SOURCE / filename), "destination_path": DEST,
        "destination_name": name, "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False,
        "import_materials": True, "import_textures": True,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False})
    options.static_mesh_import_data.set_editor_properties({"combine_meshes": True,
        "convert_scene": True, "convert_scene_unit": True, "generate_lightmap_u_vs": True,
        "auto_generate_collision": True, "remove_degenerates": True, "import_uniform_scale": 1.0})
    task.options = options
    tasks.append(task)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

rows = []
ok = True
for _, name in ROWS:
    path = f"{DEST}/{name}"
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    valid = isinstance(mesh, unreal.StaticMesh)
    ok = ok and valid
    row = {"asset": path, "loaded": valid}
    if valid:
        bounds = mesh.get_bounds()
        row["bounds_origin_cm"] = [bounds.origin.x, bounds.origin.y, bounds.origin.z]
        row["bounds_extent_cm"] = [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]
        row["material_slots"] = len(mesh.get_editor_property("static_materials"))
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    rows.append(row)
payload = {"status": "PASS__COIL_HANDLER_HYBRID_IMPORTED" if ok else "FAIL__COIL_HANDLER_IMPORT",
    "assets": rows, "protected_map_edited": False}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COIL_HANDLER_IMPORT_V999 " + payload["status"])
if not ok:
    raise RuntimeError(payload["status"])
