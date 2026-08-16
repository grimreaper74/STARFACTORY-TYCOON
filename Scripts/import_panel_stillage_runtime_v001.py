import unreal
import json
import os

PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
SOURCE = os.path.join(PROJECT, "SourceAssets", "Candidate", "WeldShop",
                      "PanelStillage_RuntimeDerivation_v001", "Exports",
                      "SM_LB_PanelStillage_Runtime_v001.fbx")
DESTINATION = "/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001"
ASSET_NAME = "SM_LB_PanelStillage_Runtime_v001"
RECEIPT = os.path.join(PROJECT, "Saved", "Audits", "WeldShop",
                       "PanelStillageRuntime_v001", "import_receipt_v001.json")

if not os.path.isfile(SOURCE):
    raise RuntimeError("Missing frozen runtime FBX: " + SOURCE)
if unreal.EditorAssetLibrary.does_asset_exist(DESTINATION + "/" + ASSET_NAME):
    raise RuntimeError("Destination already exists; refusing replacement")

task = unreal.AssetImportTask()
task.filename = SOURCE
task.destination_path = DESTINATION
task.destination_name = ASSET_NAME
task.automated = True
task.replace_existing = False
task.save = True
task.options = unreal.FbxImportUI()
task.options.import_mesh = True
task.options.import_textures = True
task.options.import_materials = True
task.options.import_as_skeletal = False
task.options.static_mesh_import_data.combine_meshes = True
task.options.static_mesh_import_data.auto_generate_collision = False

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
asset_path = DESTINATION + "/" + ASSET_NAME + "." + ASSET_NAME
mesh = unreal.load_asset(asset_path)
if not mesh:
    raise RuntimeError("Static mesh import failed")
mesh.set_editor_property("nanite_settings", unreal.NaniteSettings(enabled=False))
mesh.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)

bounds = mesh.get_bounds()
materials = [str(item.material_interface.get_path_name()) if item.material_interface else ""
             for item in mesh.static_materials]
if mesh.get_num_lods() != 1 or not materials or any(not item for item in materials):
    raise RuntimeError("Imported mesh violates LOD/material contract")

os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
receipt = {
    "status": "PASS__FRESH_PANEL_STILLAGE_RUNTIME_IMPORT",
    "asset": asset_path,
    "source": SOURCE,
    "lods": mesh.get_num_lods(),
    "bounds": str(bounds),
    "materials": materials,
    "nanite": False,
    "collision": "DEFAULT__RUNTIME_COMPONENT_FORCES_NO_COLLISION",
}
with open(RECEIPT, "w", encoding="utf-8") as handle:
    json.dump(receipt, handle, indent=2)
unreal.log("LINE_BOSS_PANEL_STILLAGE_IMPORT " + json.dumps(receipt))
