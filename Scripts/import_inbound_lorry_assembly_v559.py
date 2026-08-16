"""Isolated Unreal intake for the additive detailed four-coil lorry v002."""
from pathlib import Path
import hashlib
import json
import unreal

project = Path(unreal.Paths.project_dir())
source = project / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryAssembly_v002/FBX/SM_CA_MW_Inbound_LorryFourCoil_v002.fbx"
dest = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v004"
name = "SM_CA_MW_Inbound_LorryFourCoil_v004"
if not source.exists():
    raise RuntimeError(f"Missing detailed lorry FBX: {source}")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(source), "destination_path": dest,
    "destination_name": name, "automated": True,
    "replace_existing": True, "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True, "import_as_skeletal": False,
    "import_materials": True, "import_textures": False,
    "create_physics_asset": False, "automated_import_should_detect_type": False,
})
options.static_mesh_import_data.set_editor_properties({
    "combine_meshes": True, "generate_lightmap_u_vs": True,
    "auto_generate_collision": True, "convert_scene": True,
    "convert_scene_unit": True,
})
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

asset_path = f"{dest}/{name}"
mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Detailed lorry import failed: {asset_path}")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
size = mesh.get_bounds().box_extent * 2
bounds = [float(size.x), float(size.y), float(size.z)]
ordered = sorted(bounds)
if not 230 <= ordered[0] <= 460 or not 300 <= ordered[1] <= 560 or not 1300 <= ordered[2] <= 2300:
    raise RuntimeError(f"Unexpected detailed lorry bounds: {bounds}")
entries = mesh.get_editor_property("static_materials")
slots = [str(entry.get_editor_property("material_slot_name")) for entry in entries]
if len(slots) < 8:
    raise RuntimeError(f"Detailed lorry material separation lost: {slots}")
if mesh.get_editor_property("body_setup") is None:
    raise RuntimeError("Detailed lorry has no body setup")
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

audit = project / "Saved/Audits/PressShopIntegration/inbound_lorry_detailed_import_v559.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "status": "PASS__TECHNICAL_INTAKE_ONLY__NOT_PROMOTED",
    "asset": asset_path,
    "configuration": "detailed European cab-over plus open trailer carrying exactly four restrained coils",
    "bounds_cm": [round(v, 3) for v in bounds],
    "material_slots": slots,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "engineering_values": "TBC",
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DETAILED_LORRY_V559_IMPORT_PASS")
