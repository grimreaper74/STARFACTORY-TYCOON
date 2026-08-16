"""Read-only parameter audit for the retained roof material and its master."""

import json
from pathlib import Path

import unreal


ASSETS = [
    "/Game/LineBoss/Candidates/PressShop/ShellReadability_v238/Materials/MI_CA_MW_IndustrialGraphiteRoof_v238",
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003",
]
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_roof_material_parameters_v242.json"
library = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
rows = []
for path in ASSETS:
    asset = library.load_asset(path)
    rows.append({
        "asset": path,
        "loaded": asset is not None,
        "scalar_parameters": [str(value) for value in mel.get_scalar_parameter_names(asset)] if asset else [],
        "vector_parameters": [str(value) for value in mel.get_vector_parameter_names(asset)] if asset else [],
        "texture_parameters": [str(value) for value in mel.get_texture_parameter_names(asset)] if asset else [],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
unreal.SystemLibrary.quit_editor()
