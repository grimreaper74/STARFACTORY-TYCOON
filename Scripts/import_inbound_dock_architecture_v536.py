"""Isolated Unreal intake for inbound dock architecture v001."""
from pathlib import Path
import hashlib, json
import unreal

project = Path(unreal.Paths.project_dir())
source = project / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/DockArchitecture_v001/SM_CA_MW_Inbound_DockArchitecture_v001.fbx"
dest = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v001"
name = "SM_CA_MW_Inbound_DockArchitecture_v001"
if not source.exists():
    raise RuntimeError(f"Missing dock architecture FBX: {source}")

task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(source), "destination_path": dest, "destination_name": name,
                            "automated": True, "replace_existing": True, "save": True})
options = unreal.FbxImportUI()
options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False, "import_materials": True,
                               "import_textures": False, "create_physics_asset": False,
                               "automated_import_should_detect_type": False})
options.static_mesh_import_data.set_editor_properties({"combine_meshes": True, "generate_lightmap_u_vs": True,
                                                        "auto_generate_collision": True, "convert_scene": True,
                                                        "convert_scene_unit": True})
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

asset_path = f"{dest}/{name}"
mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Dock architecture import failed: {asset_path}")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
size = mesh.get_bounds().box_extent * 2
bounds = [float(size.x), float(size.y), float(size.z)]
ordered = sorted(bounds)
if not 600 <= ordered[0] <= 900:
    raise RuntimeError(f"Dock architecture narrow dimension unexpected: {ordered[0]:.2f} cm")
if not 600 <= ordered[1] <= 900:
    raise RuntimeError(f"Dock architecture height/depth unexpected: {ordered[1]:.2f} cm")
if not 1100 <= ordered[2] <= 1400:
    raise RuntimeError(f"Dock architecture width unexpected: {ordered[2]:.2f} cm")
slots = len(mesh.get_editor_property("static_materials"))
if slots < 7:
    raise RuntimeError(f"Dock architecture material separation lost: {slots} slots")
body = mesh.get_editor_property("body_setup") is not None
if not body:
    raise RuntimeError("Dock architecture has no body setup")
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

audit = project / "Saved/Audits/PressShopIntegration/inbound_dock_architecture_import_v536.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "status": "PASS__TECHNICAL_INTAKE_ONLY__NOT_PROMOTED", "asset": asset_path,
    "bounds_cm": [round(v, 3) for v in bounds], "material_slots": slots,
    "has_body_setup": body, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "reference_pack": "SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807",
    "engineering_values": "TBC"
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DOCK_ARCHITECTURE_V536_IMPORT_PASS")
