"""Reimport the coherent four-coil inbound lorry after FBX smoothing cleanup."""
from pathlib import Path
import hashlib
import json
import unreal

project = Path(unreal.Paths.project_dir())
source = project / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryAssembly_v001/FBX/SM_CA_MW_Inbound_LorryFourCoil_v001.fbx"
dest = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v001"
name = "SM_CA_MW_Inbound_LorryFourCoil_v001"
if not source.exists():
    raise RuntimeError(f"Missing coherent lorry FBX: {source}")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(source),
    "destination_path": dest,
    "destination_name": name,
    "automated": True,
    "replace_existing": True,
    "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True,
    "import_as_skeletal": False,
    "import_materials": True,
    "import_textures": False,
    "create_physics_asset": False,
    "automated_import_should_detect_type": False,
})
options.static_mesh_import_data.set_editor_properties({
    "combine_meshes": True,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": True,
    "convert_scene": True,
    "convert_scene_unit": True,
})
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

asset_path = f"{dest}/{name}"
mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Coherent lorry import failed: {asset_path}")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

size = mesh.get_bounds().box_extent * 2
bounds = [float(size.x), float(size.y), float(size.z)]
ordered = sorted(bounds)
if not 230.0 <= ordered[0] <= 450.0:
    raise RuntimeError(f"Unexpected coherent lorry narrow dimension: {ordered[0]:.2f} cm")
if not 300.0 <= ordered[1] <= 550.0:
    raise RuntimeError(f"Unexpected coherent lorry height/width dimension: {ordered[1]:.2f} cm")
if not 1300.0 <= ordered[2] <= 2300.0:
    raise RuntimeError(f"Unexpected coherent lorry length: {ordered[2]:.2f} cm")
slots = len(mesh.get_editor_property("static_materials"))
if slots < 6:
    raise RuntimeError(f"Coherent lorry material separation lost: {slots} slots")
body = mesh.get_editor_property("body_setup") is not None
if not body:
    raise RuntimeError("Coherent lorry has no body setup")
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

audit = project / "Saved/Audits/PressShopIntegration/inbound_lorry_assembly_import_v533.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "status": "PASS__TECHNICAL_INTAKE_ONLY__NOT_PROMOTED",
    "revision": "v533_smoothing_cleanup",
    "asset": asset_path,
    "configuration": "one coherent European cab-over and open trailer carrying exactly four restrained coils",
    "bounds_cm": [round(v, 3) for v in bounds],
    "material_slots": slots,
    "has_body_setup": body,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "engineering_values": "TBC",
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_LORRY_ASSEMBLY_V533_IMPORT_PASS")
