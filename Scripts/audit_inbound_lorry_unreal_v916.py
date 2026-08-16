import json
from pathlib import Path
import unreal

ASSET = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_InboundLorry_Approved_v006"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_lorry_unreal_v916.json"
mesh = unreal.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Missing static mesh {ASSET}")
bounds = mesh.get_bounds()
materials = []
for slot in mesh.get_editor_property("static_materials"):
    material = slot.get_editor_property("material_interface")
    materials.append(material.get_path_name() if material else None)
payload = {
    "status": "PASS__APPROVED_LORRY_UNREAL_ASSET_PRESENT__BINDING_READY",
    "asset": ASSET,
    "origin_cm": list(bounds.origin.to_tuple()),
    "box_extent_cm": list(bounds.box_extent.to_tuple()),
    "sphere_radius_cm": bounds.sphere_radius,
    "materials": materials,
    "meshy_credits_used": 0,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_INBOUND_LORRY_UNREAL_V916_PASS {payload}")
unreal.SystemLibrary.quit_editor()
