"""Report parameter names for compiled Engine materials usable as HMI capture parents."""

import json
from pathlib import Path
import unreal

paths = [
    "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial",
    "/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial",
    "/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial",
    "/Engine/ArtTools/RenderToTexture/Materials/Debug/M_BaseColor_Constant.M_BaseColor_Constant",
    "/Engine/ArtTools/RenderToTexture/Materials/Debug/M_Emissive_Color.M_Emissive_Color",
    "/Engine/EditorMaterials/Dataflow/M_Dataflow_Color.M_Dataflow_Color",
]
rows = []
for path in paths:
    material = unreal.load_asset(path)
    rows.append({
        "path": path,
        "loaded": material is not None,
        "vector_parameters": [str(x) for x in unreal.MaterialEditingLibrary.get_vector_parameter_names(material)] if material else [],
        "scalar_parameters": [str(x) for x in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material)] if material else [],
    })
out = Path(unreal.Paths.project_saved_dir()) / "Audits/engine_material_parameters.json"
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_ENGINE_MATERIAL_AUDIT_PASS path={out}")
