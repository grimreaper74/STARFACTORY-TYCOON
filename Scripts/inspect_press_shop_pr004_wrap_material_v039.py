"""Read-only parameter audit for the retained v039 packaged-coil wrap."""

import json
from pathlib import Path

import unreal


PATHS = [
    "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v029/MI_LB_MasterCoil_SatinGreyWrap_v029",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v030/MI_LB_MasterCoil_SatinGreyWrap_v030",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v034/MI_LB_MasterCoil_WovenGreyWrap_v034",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v034/MI_LB_MasterCoil_WrapOverlap_v034",
]
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_wrap_material_inventory_v039.json"
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
rows = []
for path in PATHS:
    asset = lib.load_asset(path)
    if asset is None:
        rows.append({"path": path, "missing": True})
        continue
    row = {"path": path, "parent": asset.get_editor_property("parent").get_path_name(), "scalars": {}, "vectors": {}, "textures": {}}
    for name in mel.get_scalar_parameter_names(asset):
        row["scalars"][str(name)] = mel.get_material_instance_scalar_parameter_value(asset, name)
    for name in mel.get_vector_parameter_names(asset):
        value = mel.get_material_instance_vector_parameter_value(asset, name)
        row["vectors"][str(name)] = [value.r, value.g, value.b, value.a]
    for name in mel.get_texture_parameter_names(asset):
        value = mel.get_material_instance_texture_parameter_value(asset, name)
        row["textures"][str(name)] = value.get_path_name() if value else None
    rows.append(row)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_WRAP_MATERIAL_AUDIT_PASS output={OUT}")
unreal.SystemLibrary.quit_editor()
