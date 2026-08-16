"""Read-only parameter inventory for the floor materials visible in v103."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/floor_material_parameter_inspection_v103.json"
paths = [
    "/Game/LineBoss/Materials/M_LB_FactoryConcrete",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_COIL_STORE",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_FRONT_END",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_LOGISTICS",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_RECEIVING",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_SUPPORT",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_TOOLING",
    "/Game/LineBoss/Materials/M_LB_Zone_PRESS_TRAINS",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Hold_Red",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR001_Blue",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR002_Orange",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR003_BlueGreen",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Walkway_Green",
]
lib = unreal.EditorAssetLibrary
rows = []
for path in paths:
    asset = lib.load_asset(path)
    if asset is None:
        rows.append({"path": path, "missing": True})
        continue
    row = {
        "path": path,
        "class": asset.get_class().get_name(),
        "parent": None,
        "scalar_parameters": [],
        "vector_parameters": [],
        "texture_parameters": [],
    }
    try:
        parent = asset.get_editor_property("parent")
        row["parent"] = parent.get_path_name() if parent else None
    except Exception:
        pass
    for key, method in (
        ("scalar_parameters", unreal.MaterialEditingLibrary.get_scalar_parameter_names),
        ("vector_parameters", unreal.MaterialEditingLibrary.get_vector_parameter_names),
        ("texture_parameters", unreal.MaterialEditingLibrary.get_texture_parameter_names),
    ):
        try:
            row[key] = [str(value) for value in method(asset)]
        except Exception as exc:
            row[key + "_error"] = str(exc)
    rows.append(row)

payload = {
    "$schema": "cairnwell/audit/press-shop-floor-material-parameter-inspection-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_PARAMETER_INVENTORY__NO_ASSETS_CHANGED",
    "materials": rows,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
