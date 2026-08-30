"""Import the verified S02 portal press as a new Unreal asset only."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "S02_PortalPress_MeshyClean_v001" / "Runtime" / "SM_LB_PS_S02_PortalPress_MeshyClean_v001.fbx"
DEST = "/Game/LineBoss/Candidates/PressShop/S02PortalPressMeshyClean_v001"
ASSET_PATH = DEST + "/SM_LB_PS_S02_PortalPress_MeshyClean_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "s02_portal_press_meshy_import_v001.json"

if not SOURCE.is_file():
    raise RuntimeError("Verified S02 portal FBX is missing")
if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
    raise RuntimeError("Refusing to overwrite an existing S02 portal Unreal asset")

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_as_skeletal", False)
ui.set_editor_property("import_materials", True)
ui.set_editor_property("import_textures", True)
ui.set_editor_property("automated_import_should_detect_type", False)
ui.static_mesh_import_data.set_editor_property("combine_meshes", True)
ui.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
ui.static_mesh_import_data.set_editor_property("auto_generate_collision", True)

task = unreal.AssetImportTask()
task.set_editor_property("filename", str(SOURCE))
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", "SM_LB_PS_S02_PortalPress_MeshyClean_v001")
task.set_editor_property("options", ui)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", False)
task.set_editor_property("save", True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
if not unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
    raise RuntimeError("S02 portal FBX import produced no named static mesh")
mesh = unreal.load_asset(ASSET_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Imported S02 portal asset is not a StaticMesh")
extent = mesh.get_bounds().box_extent
if min(extent.x, extent.y, extent.z) <= 1.0:
    raise RuntimeError("Imported S02 portal mesh has invalid bounds")
unreal.EditorAssetLibrary.save_asset(ASSET_PATH, only_if_is_dirty=False)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__S02_PORTAL_PRESS_UNREAL_IMPORT_V001",
    "source_fbx": str(SOURCE),
    "source_fbx_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "asset": ASSET_PATH,
    "bounds_extent_cm": [round(extent.x, 3), round(extent.y, 3), round(extent.z, 3)],
    "materials": [str(material) for material in mesh.get_materials()],
    "collision": "Unreal auto-generated candidate; must be reviewed in-engine",
}, indent=2), encoding="utf-8")
unreal.log("S02_PORTAL_PRESS_UNREAL_IMPORT_V001_PASS")
unreal.SystemLibrary.quit_editor()
