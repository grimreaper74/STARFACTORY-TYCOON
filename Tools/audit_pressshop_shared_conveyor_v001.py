"""Read-only bounds check for the existing shared press-shop conveyor asset."""
import json
from pathlib import Path
import unreal

PATH = "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits" / "PressShopIntegration" / "pressshop_shared_conveyor_audit_v001.json"
mesh = unreal.load_asset(PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Shared powered conveyor asset unavailable")
bounds = mesh.get_bounds()
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__SHARED_POWERED_CONVEYOR_AUDIT",
    "asset": PATH,
    "extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
    "origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
    "materials": [str(row.material_interface) for row in mesh.get_editor_property("static_materials")],
}, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
