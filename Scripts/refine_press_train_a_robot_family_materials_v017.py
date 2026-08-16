"""Give isolated v017 a restrained matte Cairnwell robot-family finish."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
editing = unreal.MaterialEditingLibrary
material_root = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials"
out = root / "Saved/Audits/PressTrains/press_train_a_robot_family_material_refine_v017.json"
map_file = root / "Content/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017.umap"
protected = {
    "v013": (root / "Content/LineBoss/Maps/LB_PressTrainASightlineCandidate_v013.umap",
             "24DB4253EB910A1282891F38CA52D6A8B5A93E2D01E1ECE9006A57CF12A56683"),
    "v107": (root / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap",
             "E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77"),
    "v213": (root / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap",
             "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rebuild(path, colour, metallic, roughness, specular):
    material = library.load_asset(path)
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Expected Material at {path}")
    editing.delete_all_material_expressions(material)
    colour_node = editing.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -120)
    colour_node.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    editing.connect_material_property(colour_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    values = (
        (metallic, unreal.MaterialProperty.MP_METALLIC, -520, 40),
        (roughness, unreal.MaterialProperty.MP_ROUGHNESS, -520, 140),
        (specular, unreal.MaterialProperty.MP_SPECULAR, -520, 240),
    )
    for value, target, x, y in values:
        node = editing.create_material_expression(material, unreal.MaterialExpressionConstant, x, y)
        node.set_editor_property("r", value)
        editing.connect_material_property(node, "", target)
    errors = [str(value) for value in editing.recompile_material(material)]
    if errors:
        raise RuntimeError(f"Material compile errors for {path}: {errors}")
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return {"asset": path, "colour_linear": colour, "metallic": metallic,
            "roughness": roughness, "specular": specular}


map_hash_before = sha(map_file)
rows = [
    rebuild(material_root + "/M_CA_MW_PTA_Charcoal_AssemblyStudyRobotFamily_v017",
            (0.032, 0.042, 0.047), 0.38, 0.58, 0.32),
    rebuild(material_root + "/M_CA_MW_PTA_RobotSafetyYellow_AssemblyStudyRobotFamily_v017",
            (0.52, 0.075, 0.008), 0.32, 0.43, 0.36),
]
failures = []
if sha(map_file) != map_hash_before:
    failures.append("v017 map changed during material-only refinement")
protected_hashes = {}
for name, (path, expected) in protected.items():
    actual = sha(path)
    protected_hashes[name] = actual
    if actual != expected:
        failures.append(f"protected {name} changed: {actual}")
report = {
    "$schema": "cairnwell/audit/press-train-a-robot-family-material-refine-v017/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V017_MATTE_CHARCOAL_ORANGE_ROBOT_FAMILY_MATERIALS__VISUAL_REGATE_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__V017_ROBOT_FAMILY_MATERIAL_REFINE__NOT_PROMOTED",
    "map_sha256": map_hash_before, "materials": rows,
    "protected_map_hashes": protected_hashes, "failures": failures,
    "engineering_values_changed": False, "production_map_changed": False,
    "promotion_authorized": False,
}
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
