"""Create a lorry-only bright wrapped-steel material and additive mesh candidate."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
mat_dir = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v003/Materials"
mat_path = f"{mat_dir}/M_CA_Inbound_BrightWrappedSteel_v001"
mesh_source = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v002/SM_CA_MW_Inbound_LorryFourCoil_v002"
mesh_path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v003/SM_CA_MW_Inbound_LorryFourCoil_v003"

for path in (mesh_path, mat_path):
    if library.does_asset_exist(path):
        library.delete_asset(path)

material = tools.create_asset("M_CA_Inbound_BrightWrappedSteel_v001", mat_dir, unreal.Material, unreal.MaterialFactoryNew())
base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, 0)
base.set_editor_property("constant", unreal.LinearColor(0.70, 0.76, 0.82, 1.0))
rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 140)
rough.set_editor_property("r", 0.34)
metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 250)
metal.set_editor_property("r", 0.68)
mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
mel.recompile_material(material)
library.save_loaded_asset(material, only_if_is_dirty=False)

if not library.duplicate_asset(mesh_source, mesh_path):
    raise RuntimeError("Failed duplicating additive lorry v003")
mesh = library.load_asset(mesh_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Lorry v003 is not a StaticMesh")
steel_indices = []
for index, entry in enumerate(mesh.get_editor_property("static_materials")):
    if str(entry.get_editor_property("material_slot_name")) == "MI_CA_Inbound_BrushedSteel":
        mesh.set_material(index, material)
        steel_indices.append(index)
if steel_indices != [5]:
    raise RuntimeError(f"Unexpected lorry steel slots: {steel_indices}")
library.save_loaded_asset(mesh, only_if_is_dirty=False)

out = project / "Saved/Audits/PressShopIntegration/inbound_lorry_bright_wrap_candidate_v547.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "status": "PASS__ADDITIVE_LORRY_BRIGHT_WRAP_CANDIDATE__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_mesh": mesh_source,
    "candidate_mesh": mesh_path,
    "dedicated_material": mat_path,
    "base_color": [0.70, 0.76, 0.82],
    "roughness": 0.34,
    "metallic": 0.68,
    "steel_slot_indices": steel_indices,
    "engineering_values": "TBC",
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_LORRY_BRIGHT_WRAP_V547_PASS")
