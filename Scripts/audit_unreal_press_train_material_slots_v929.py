import unreal
import json
from pathlib import Path

roots = [
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260810_v927/CupTransfer",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v788/S07ConnectedVacuumTool",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v015/TexturedModules/Station",
]
assets = []
for root in roots:
    for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        slots = []
        for slot in asset.get_editor_property("static_materials"):
            interface = slot.get_editor_property("material_interface")
            slots.append({
                "slot_name": str(slot.get_editor_property("material_slot_name")),
                "imported_slot_name": str(slot.get_editor_property("imported_material_slot_name")),
                "material": interface.get_path_name() if interface else None,
            })
        assets.append({"mesh": path, "slots": slots})

out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\unreal_material_slots_v929.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"roots": roots, "assets": assets}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_UNREAL_MATERIAL_SLOT_AUDIT_V929 {out}")
