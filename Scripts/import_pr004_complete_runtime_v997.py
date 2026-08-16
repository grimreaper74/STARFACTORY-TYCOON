import json
from pathlib import Path
import unreal

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Runtime_v997"
DEST = "/Game/LineBoss/Runtime/PressShop/PR004_v997"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/pr004_unreal_import_v997.json"
ROWS = (
    ("SM_Cairnwell_PR004_CompleteCell_Runtime_v997.fbx", "SM_Cairnwell_PR004_CompleteCell_Runtime_v997"),
    ("SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997.fbx", "SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997"),
)

tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for filename, name in ROWS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / filename), "destination_path": DEST,
        "destination_name": name, "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": True,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False})
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": True,
        "remove_degenerates": True, "import_uniform_scale": 1.0})
    task.options = options
    tasks.append(task)

tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

rows = []
ok = True
for _, name in ROWS:
    path = f"{DEST}/{name}"
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    exists = isinstance(mesh, unreal.StaticMesh)
    ok = ok and exists
    row = {"asset": path, "loaded": exists}
    if exists:
        bounds = mesh.get_bounds()
        row.update({
            "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
            "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
            "material_slots": len(mesh.get_editor_property("static_materials")),
        })
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    rows.append(row)

payload = {
    "status": "PASS__PR004_RUNTIME_ASSETS_IMPORTED" if ok else "FAIL__PR004_RUNTIME_IMPORT_INCOMPLETE",
    "destination": DEST, "assets": rows, "protected_map_edited": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR004_UNREAL_IMPORT_V997 " + payload["status"])
if not ok:
    raise RuntimeError(payload["status"])
