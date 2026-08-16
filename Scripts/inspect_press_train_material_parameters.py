"""Read-only diagnostic of inherited Press Shop material parameters."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/press_train_material_parameter_diagnostic.json"
paths = {
    "charcoal": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "green": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "service_grey": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "worked_steel": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_MachinedSteel_v085",
}
records = {}
for key, path in paths.items():
    material = unreal.EditorAssetLibrary.load_asset(path)
    records[key] = {
        "path": path,
        "class": material.get_class().get_name() if material else None,
        "scalar_parameters": [str(value) for value in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material)] if material else [],
        "vector_parameters": [str(value) for value in unreal.MaterialEditingLibrary.get_vector_parameter_names(material)] if material else [],
        "texture_parameters": [str(value) for value in unreal.MaterialEditingLibrary.get_texture_parameter_names(material)] if material else [],
    }
report = {
    "$schema": "cairnwell/diagnostic/press-train-material-parameters/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "records": records,
    "mutated_assets": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
