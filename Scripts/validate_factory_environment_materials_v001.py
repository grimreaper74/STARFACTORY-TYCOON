"""Independent validation for the v001 world-space factory floor materials.

This script is deliberately read-only: it loads the master material, inspects
saved output links and material-instance overrides, and writes a Saved audit
receipt.  It does not save or mutate either asset.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
MASTER_PACKAGE = "/Game/LineBoss/Materials/Environment/M_LB_SealedFactoryConcrete_World_v001"
INSTANCE_PACKAGE = "/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001"
MASTER_OBJECT = f"{MASTER_PACKAGE}.{MASTER_PACKAGE.rsplit('/', 1)[-1]}"
INSTANCE_OBJECT = f"{INSTANCE_PACKAGE}.{INSTANCE_PACKAGE.rsplit('/', 1)[-1]}"
AUDIT = ROOT / "Saved/Audits/VisualTuning/factory_environment_materials_v001_validation.json"


def object_path(value):
    return value.get_path_name() if value is not None else None


def get_property(owner, name):
    try:
        return owner.get_editor_property(name)
    except Exception:
        return None


def scalar_value(instance, name):
    return float(unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(instance, name))


def vector_value(instance, name):
    value = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(instance, name)
    return [float(value.r), float(value.g), float(value.b), float(value.a)]


checks = []


def check(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


library = unreal.EditorAssetLibrary
registry = unreal.AssetRegistryHelpers.get_asset_registry()
master = library.load_asset(MASTER_OBJECT)
instance = library.load_asset(INSTANCE_OBJECT)

check("master_exists", master is not None and library.does_asset_exist(MASTER_PACKAGE), object_path(master))
check("instance_exists", instance is not None and library.does_asset_exist(INSTANCE_PACKAGE), object_path(instance))
check("master_class", isinstance(master, unreal.Material), master.get_class().get_name() if master else None)
check(
    "instance_class",
    isinstance(instance, unreal.MaterialInstanceConstant),
    instance.get_class().get_name() if instance else None,
)

master_data = registry.get_asset_by_object_path(unreal.Name(MASTER_OBJECT))
instance_data = registry.get_asset_by_object_path(unreal.Name(INSTANCE_OBJECT))
check("master_asset_registry", master_data.is_valid(), str(master_data))
check("instance_asset_registry", instance_data.is_valid(), str(instance_data))

master_filename = Path(unreal.PackageTools.package_name_to_filename(MASTER_PACKAGE, ".uasset"))
instance_filename = Path(unreal.PackageTools.package_name_to_filename(INSTANCE_PACKAGE, ".uasset"))
check("master_package_file", master_filename.exists(), str(master_filename))
check("instance_package_file", instance_filename.exists(), str(instance_filename))

# Python does not expose the private UMaterial expression collection in this
# UE 5.8 build, so use the supported MaterialEditingLibrary output inspection.
# These exact node classes prove the saved asset retained its three output
# connections; shader-compile errors are separately gated from the log.
property_links = {}
get_input = getattr(unreal.MaterialEditingLibrary, "get_material_property_input_node", None)
if get_input:
    for label, prop in {
        "base_color": unreal.MaterialProperty.MP_BASE_COLOR,
        "roughness": unreal.MaterialProperty.MP_ROUGHNESS,
        "metallic": unreal.MaterialProperty.MP_METALLIC,
    }.items():
        try:
            node = get_input(master, prop)
            property_links[label] = object_path(node)
        except Exception as exc:
            property_links[label] = f"ERROR: {exc}"
check(
    "material_output_links",
    str(property_links.get("base_color", "")).endswith(":MaterialExpressionLinearInterpolate_0")
    and str(property_links.get("roughness", "")).endswith(":MaterialExpressionScalarParameter_5")
    and str(property_links.get("metallic", "")).endswith(":MaterialExpressionConstant_0"),
    property_links,
)

parent = get_property(instance, "parent")
check("instance_parent", object_path(parent) == MASTER_OBJECT, object_path(parent))

expected_scalars = {
    "MacroVariationStrength": 0.055,
    "FineVariationStrength": 0.020,
    "SlabSizeCm": 600.0,
    "JointHalfWidthRatio": 0.0025,
    "JointSoftnessRatio": 0.0030,
    "Roughness": 0.82,
}
actual_scalars = {name: scalar_value(instance, name) for name in expected_scalars}
check(
    "instance_scalar_values",
    all(abs(actual_scalars[name] - expected) <= 0.0001 for name, expected in expected_scalars.items()),
    actual_scalars,
)

expected_vectors = {
    "ConcreteTint": [0.285, 0.305, 0.315, 1.0],
    "JointTint": [0.095, 0.105, 0.11, 1.0],
}
actual_vectors = {name: vector_value(instance, name) for name in expected_vectors}
check(
    "instance_vector_values",
    all(
        all(abs(actual - expected) <= 0.0001 for actual, expected in zip(actual_vectors[name], values))
        for name, values in expected_vectors.items()
    ),
    actual_vectors,
)

default_game = (ROOT / "Config/DefaultGame.ini").read_text(encoding="utf-8")
always_cook_line = '+DirectoriesToAlwaysCook=(Path="/Game/LineBoss/Materials/Environment")'
check("always_cook_directory", always_cook_line in default_game, always_cook_line)

result = {
    "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
    "master": MASTER_OBJECT,
    "instance": INSTANCE_OBJECT,
    "checks": checks,
    "note": "UE 5.8 Python does not expose the private expression collection. Saved output nodes are inspected through MaterialEditingLibrary; compile diagnostics are evaluated from the commandlet log and runtime material load/compile.",
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")

if result["status"] == "PASS":
    unreal.log(f"LINE_BOSS_FACTORY_ENVIRONMENT_VALIDATION_PASS audit={AUDIT}")
else:
    failed = [item["name"] for item in checks if not item["passed"]]
    unreal.log_error(f"LINE_BOSS_FACTORY_ENVIRONMENT_VALIDATION_FAIL failed={failed} audit={AUDIT}")
