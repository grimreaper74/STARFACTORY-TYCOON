"""Read-only post-import audit for the native textured S02 Deep Draw v003 set.

The importer receipt proves how the package was made.  This separate process
proves the current saved packages still contain the intended 46 texture assets,
master defaults, 15 material-instance overrides, and normal-map conversion.
Only this audit receipt is written; no Content, map, or source asset is changed.
"""

from __future__ import annotations

import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
CONTENT_ROOT = PROJECT_ROOT / "Content/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003"
AUDIT_DIR = PROJECT_ROOT / "Saved/Audits/OneFactory/Press/S02DeepDrawRuntimePrep_v003"
RECEIPT = AUDIT_DIR / "material_runtime_audit_retry1.json"

DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v003"
)
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
MASTER_NAME = "M_CA_S02DeepDraw_PBR_Master_v003"
MASTER_PATH = f"{MATERIAL_DESTINATION}/{MASTER_NAME}.{MASTER_NAME}"

FAMILY_TUNING = {
    "MainGreen": {"dust": 0.07, "emission": 0.0},
    "Concrete": {"dust": 0.05, "emission": 0.0},
    "DarkSteel": {"dust": 0.04, "emission": 0.0},
    "CleanSteel": {"dust": 0.025, "emission": 0.0},
    "CharcoalGrey": {"dust": 0.045, "emission": 0.0},
    "SafetyYellow": {"dust": 0.035, "emission": 0.0},
    "ScreenDark": {"dust": 0.01, "emission": 0.0},
    "LampGreen": {"dust": 0.0, "emission": 1.5},
    "LampAmber": {"dust": 0.0, "emission": 1.2},
    "LampRed": {"dust": 0.0, "emission": 0.75},
}
MODULE_SLOTS = {
    "Static": (
        "MainGreen", "Concrete", "DarkSteel", "CleanSteel", "CharcoalGrey",
        "SafetyYellow", "ScreenDark", "LampGreen", "LampAmber", "LampRed",
    ),
    "Ram": ("DarkSteel",),
    "Blankholder": ("CleanSteel",),
    "Bolster": ("CleanSteel",),
    "Flywheel": ("DarkSteel",),
    "SafetyGate": ("SafetyYellow",),
}
CHANNELS = ("BC", "N", "ORM", "MASK")
TEXTURE_PARAMETERS = {
    "BaseColorMap": "BC",
    "NormalMap": "N",
    "ORMMap": "ORM",
    "WearMaskMap": "MASK",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def object_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def package_from_object_path(path: str) -> str:
    return path.rsplit(".", 1)[0]


def snapshot_native_packages() -> dict[str, dict[str, int | str]]:
    snapshots = {}
    for path in sorted(CONTENT_ROOT.rglob("*.uasset")):
        snapshots[str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")] = {
            "sha256": sha256(path),
            "mtime_ns": path.stat().st_mtime_ns,
        }
    return snapshots


def expected_texture_name(family: str, channel: str) -> str:
    return f"T_CA_S02_{family}_{channel}"


def expected_ao_name(module: str) -> str:
    return f"T_CA_S02_{module}_AO"


def get_path(asset) -> str:
    return str(asset.get_path_name()) if asset else "none"


def texture_check(texture, name: str, channel: str, failures: list[str]) -> dict:
    expected_srgb = channel == "BC"
    expected_compression = {
        "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
        "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
        "ORM": unreal.TextureCompressionSettings.TC_MASKS,
        "MASK": unreal.TextureCompressionSettings.TC_MASKS,
        "AO": unreal.TextureCompressionSettings.TC_MASKS,
    }[channel]
    if not texture or not isinstance(texture, unreal.Texture):
        failures.append(f"{name} does not resolve to a Texture")
        return {"path": get_path(texture), "valid": False}
    actual_srgb = bool(texture.get_editor_property("srgb"))
    actual_compression = texture.get_editor_property("compression_settings")
    actual_flip_green = bool(texture.get_editor_property("flip_green_channel"))
    if actual_srgb != expected_srgb:
        failures.append(f"{name} sRGB={actual_srgb}, expected {expected_srgb}")
    if actual_compression != expected_compression:
        failures.append(
            f"{name} compression={actual_compression}, expected {expected_compression}")
    if channel == "N" and not actual_flip_green:
        failures.append(f"{name} must retain Flip Green Channel for OpenGL normals")
    if channel != "N" and actual_flip_green:
        failures.append(f"{name} unexpectedly has Flip Green Channel enabled")
    return {
        "path": get_path(texture),
        "srgb": actual_srgb,
        "compression": str(actual_compression),
        "flip_green_channel": actual_flip_green,
        "valid": (actual_srgb == expected_srgb
                  and actual_compression == expected_compression
                  and actual_flip_green == (channel == "N")),
    }


def audit() -> dict:
    failures: list[str] = []
    before = snapshot_native_packages()
    if len(before) != 68:
        failures.append(f"expected 68 native v003 uassets, found {len(before)}")

    expected_texture_objects = {}
    for family in FAMILY_TUNING:
        for channel in CHANNELS:
            name = expected_texture_name(family, channel)
            expected_texture_objects[name] = object_path(TEXTURE_DESTINATION, name)
    for module in MODULE_SLOTS:
        name = expected_ao_name(module)
        expected_texture_objects[name] = object_path(TEXTURE_DESTINATION, name)
    if len(expected_texture_objects) != 46:
        failures.append("internal expected v003 texture closure is not exactly 46")

    actual_texture_packages = {
        package_from_object_path(str(path))
        for path in unreal.EditorAssetLibrary.list_assets(
            TEXTURE_DESTINATION, recursive=False, include_folder=False)
    }
    expected_texture_packages = {
        package_from_object_path(path) for path in expected_texture_objects.values()
    }
    if actual_texture_packages != expected_texture_packages:
        failures.append("texture namespace inventory differs from exact v003 closure")

    texture_results = {}
    textures = {}
    for name, path in sorted(expected_texture_objects.items()):
        texture = unreal.load_asset(path)
        textures[name] = texture
        channel = "AO" if name.endswith("_AO") else name.rsplit("_", 1)[1]
        texture_results[name] = texture_check(texture, name, channel, failures)

    master = unreal.load_asset(MASTER_PATH)
    if not master or not isinstance(master, unreal.Material):
        failures.append("v003 PBR master does not resolve to a Material")
    master_defaults = {}
    default_parameters = {
        "BaseColorMap": expected_texture_name("MainGreen", "BC"),
        "NormalMap": expected_texture_name("MainGreen", "N"),
        "ORMMap": expected_texture_name("MainGreen", "ORM"),
        "WearMaskMap": expected_texture_name("MainGreen", "MASK"),
        "ModuleAOMap": expected_ao_name("Static"),
    }
    if master and isinstance(master, unreal.Material):
        for parameter, texture_name in default_parameters.items():
            actual = unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(
                master, parameter)
            actual_path = get_path(actual)
            expected_path = expected_texture_objects[texture_name]
            master_defaults[parameter] = actual_path
            if actual_path != expected_path:
                failures.append(
                    f"master {parameter}={actual_path}, expected {expected_path}")
        for parameter in ("RawDustStrength", "EmissionStrength"):
            actual = float(unreal.MaterialEditingLibrary
                           .get_material_default_scalar_parameter_value(master, parameter))
            master_defaults[parameter] = actual
            if abs(actual) > 0.0001:
                failures.append(f"master {parameter}={actual}, expected 0")
        # UE 5.8 requires ComponentMask's unnamed input pin and enforces a
        # Masks sampler for TC_MASKS textures.  Verify the repaired live graph
        # rather than relying solely on material-instance parameter values.
        expected_samplers = {
            "BaseColorMap": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
            "NormalMap": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
            "ORMMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
            "WearMaskMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
            "ModuleAOMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        }
        expected_masks = {430: "ORMMap", 500: "ORMMap", 560: "ORMMap",
                          630: "WearMaskMap", 830: "ModuleAOMap"}
        expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(master))
        samples = {
            str(node.get_editor_property("parameter_name")): node
            for node in expressions
            if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D)
        }
        master_graph = {"samplers": {}, "component_mask_inputs": {}}
        if set(samples) != set(expected_samplers):
            failures.append("master texture parameter graph drifted")
        else:
            for parameter, expected_sampler in expected_samplers.items():
                actual_sampler = samples[parameter].get_editor_property("sampler_type")
                master_graph["samplers"][parameter] = str(actual_sampler)
                if actual_sampler != expected_sampler:
                    failures.append(f"master sampler type drifted: {parameter}")
        masks = [node for node in expressions
                 if isinstance(node, unreal.MaterialExpressionComponentMask)]
        by_y = {int(node.get_editor_property("material_expression_editor_y")): node
                for node in masks}
        if len(masks) != len(expected_masks) or set(by_y) != set(expected_masks):
            failures.append("master ComponentMask graph shape drifted")
        else:
            for y, expected_parameter in sorted(expected_masks.items()):
                node = by_y[y]
                inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
                    master, node))
                source = inputs[0] if len(inputs) == 1 else None
                actual_parameter = (str(source.get_editor_property("parameter_name"))
                                    if source and isinstance(
                                        source, unreal.MaterialExpressionTextureSampleParameter2D)
                                    else None)
                output = (str(unreal.MaterialEditingLibrary
                              .get_input_node_output_name_for_material_expression(node, source))
                          if source else None)
                master_graph["component_mask_inputs"][str(y)] = {
                    "source_parameter": actual_parameter, "output": output}
                if actual_parameter != expected_parameter or output != "RGB":
                    failures.append(
                        f"master ComponentMask y={y} is not wired to {expected_parameter}.RGB")
        master_defaults["runtime_graph"] = master_graph

    expected_instance_paths = {}
    instance_results = {}
    for module, families in MODULE_SLOTS.items():
        for family in families:
            name = f"MI_CA_S02DeepDraw_{module}_{family}_v003"
            instance_path = object_path(MATERIAL_DESTINATION, name)
            expected_instance_paths[name] = instance_path
            instance = unreal.load_asset(instance_path)
            result = {"path": get_path(instance), "family": family, "module": module}
            if not instance or not isinstance(instance, unreal.MaterialInstanceConstant):
                failures.append(f"{name} does not resolve to a MaterialInstanceConstant")
                instance_results[name] = result
                continue
            parent_path = get_path(instance.get_editor_property("parent"))
            result["parent"] = parent_path
            if parent_path != MASTER_PATH:
                failures.append(f"{name} parent={parent_path}, expected v003 master")
            parameter_paths = {}
            for parameter, channel in TEXTURE_PARAMETERS.items():
                actual = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                    instance, parameter)
                actual_path = get_path(actual)
                expected_path = expected_texture_objects[
                    expected_texture_name(family, channel)]
                parameter_paths[parameter] = actual_path
                if actual_path != expected_path:
                    failures.append(
                        f"{name} {parameter}={actual_path}, expected {expected_path}")
            actual_ao = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                instance, "ModuleAOMap")
            actual_ao_path = get_path(actual_ao)
            expected_ao_path = expected_texture_objects[expected_ao_name(module)]
            parameter_paths["ModuleAOMap"] = actual_ao_path
            if actual_ao_path != expected_ao_path:
                failures.append(
                    f"{name} ModuleAOMap={actual_ao_path}, expected {expected_ao_path}")
            scalars = {}
            for parameter, key in (("RawDustStrength", "dust"),
                                   ("EmissionStrength", "emission")):
                actual = float(unreal.MaterialEditingLibrary
                               .get_material_instance_scalar_parameter_value(instance, parameter))
                expected = FAMILY_TUNING[family][key]
                scalars[parameter] = actual
                if abs(actual - expected) > 0.0001:
                    failures.append(
                        f"{name} {parameter}={actual}, expected {expected}")
            result["texture_parameters"] = parameter_paths
            result["scalar_parameters"] = scalars
            instance_results[name] = result

    expected_material_packages = {
        package_from_object_path(MASTER_PATH),
        *{package_from_object_path(path) for path in expected_instance_paths.values()},
    }
    actual_material_packages = {
        package_from_object_path(str(path))
        for path in unreal.EditorAssetLibrary.list_assets(
            MATERIAL_DESTINATION, recursive=False, include_folder=False)
    }
    if actual_material_packages != expected_material_packages:
        failures.append("material namespace inventory differs from master plus 15 v003 MIs")
    if len(instance_results) != 15:
        failures.append(f"expected 15 v003 material instances, audited {len(instance_results)}")

    after = snapshot_native_packages()
    if after != before:
        failures.append("read-only material audit changed native v003 Content packages")
    return {
        "$schema": "lineboss/audit/onefactory/press/s02-deepdraw-runtimeprep-v003-materials/v1",
        "generated_utc": now(),
        "write_scope": [str(RECEIPT)],
        "content_writes": [],
        "map_loaded_or_saved": [],
        "source_or_importer_rerun": False,
        "master": {"path": get_path(master), "defaults": master_defaults},
        "texture_count": len(texture_results),
        "texture_results": texture_results,
        "material_instance_count": len(instance_results),
        "material_instances": instance_results,
        "native_package_snapshot_before": before,
        "native_package_snapshot_after": after,
        "native_packages_unchanged": after == before,
        "failures": failures,
        "status": ("PASS__S02_DEEPDRAW_V003_CURRENT_MATERIAL_CLOSURE"
                   if not failures else "FAIL__S02_DEEPDRAW_V003_CURRENT_MATERIAL_CLOSURE"),
    }


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = audit()
        RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        if result["failures"]:
            raise RuntimeError("; ".join(result["failures"]))
        unreal.log("S02_DEEPDRAW_V003_MATERIAL_AUDIT_PASS")
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        failure = {
            "$schema": "lineboss/audit/onefactory/press/s02-deepdraw-runtimeprep-v003-materials/v1",
            "generated_utc": now(),
            "status": "FAIL__S02_DEEPDRAW_V003_CURRENT_MATERIAL_CLOSURE",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "write_scope": [str(RECEIPT)],
            "content_writes": [],
            "map_loaded_or_saved": [],
            "source_or_importer_rerun": False,
        }
        RECEIPT.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        unreal.log_error("S02_DEEPDRAW_V003_MATERIAL_AUDIT_FAIL: " + str(error))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
