"""Independent read-only audit of the native textured S03--S06 StagePack v003.

This is intentionally separate from the importer.  It fresh-loads the saved
packages, proves the semantic mesh/material closure and records an important
source-topology semantic exception without changing Content, maps, or Claude's
source bundles.
"""

from __future__ import annotations

import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
CONTENT_ROOT = PROJECT_ROOT / "Content/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003"
AUDIT_DIR = PROJECT_ROOT / "Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001"
# Preserve the initial failed verifier receipt as evidence; this corrected
# enum-format comparison writes a distinct rerun record.
RECEIPT = AUDIT_DIR / "native_runtime_audit_v003_retry5.json"
IMPORTER = PROJECT_ROOT / "Tools/import_s03s06_stagepack_runtimeprep_v001.py"

DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v003"
)
MESH_DESTINATION = DESTINATION + "/Meshes"
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
MASTER_NAME = "M_CA_MW_PT_StagePack_PBR_Master_v001"
MASTER_PATH = f"{MATERIAL_DESTINATION}/{MASTER_NAME}.{MASTER_NAME}"
FAMILIES = (
    "CairnwellGreen", "FoundryCharcoal", "ServiceGrey", "SafetyYellow",
    "WorkedSteel", "InspectionGlass", "TrainAAccent", "StatusGreen",
    "StatusAmber",
)
CHANNELS = ("BC", "N", "ORM", "MASK")
FAMILY_DUST = {
    "CairnwellGreen": 0.035,
    "FoundryCharcoal": 0.050,
    "ServiceGrey": 0.030,
    "SafetyYellow": 0.020,
    "WorkedSteel": 0.015,
    "InspectionGlass": 0.0,
    "TrainAAccent": 0.020,
    "StatusGreen": 0.0,
    "StatusAmber": 0.0,
}

MESHES = {
    "S03_Frame": {
        "name": "SM_CA_MW_PT_S03_Frame_Form_LOD0_v001",
        "dimensions": (648.0, 620.0, 950.0),
        "unreal_triangles": 8496,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    "S03_Cue": {
        "name": "SM_CA_MW_PT_S03_Cue_SecondaryForm_LOD0_v001",
        "dimensions": (56.5, 222.0, 178.0),
        "unreal_triangles": 2432,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
            "CA_MW_CairnwellGreen", "CA_MW_WorkedSteel",
            "CA_MW_TrainAAccent", "CA_MW_SafetyYellow",
            "CA_MW_StatusGreen",
        ),
    },
    "S04_Frame": {
        "name": "SM_CA_MW_PT_S04_Frame_Trim_LOD0_v001",
        "dimensions": (648.0, 620.0, 900.0),
        "unreal_triangles": 8700,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    "S04_Cue": {
        "name": "SM_CA_MW_PT_S04_Cue_TrimScrap_LOD0_v001",
        "dimensions": (68.0, 232.0, 225.0),
        "unreal_triangles": 972,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
            "CA_MW_SafetyYellow", "CA_MW_CairnwellGreen",
            "CA_MW_WorkedSteel", "CA_MW_StatusAmber",
        ),
    },
    "S05_Frame": {
        "name": "SM_CA_MW_PT_S05_Frame_Pierce_LOD0_v001",
        "dimensions": (648.0, 620.0, 850.0),
        "unreal_triangles": 8700,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    "S05_Cue": {
        "name": "SM_CA_MW_PT_S05_Cue_PierceSlug_LOD0_v001",
        "dimensions": (71.5, 226.0, 224.0),
        "unreal_triangles": 1956,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
            "CA_MW_CairnwellGreen", "CA_MW_StatusAmber",
            "CA_MW_SafetyYellow", "CA_MW_WorkedSteel",
        ),
    },
    "S06_Frame": {
        "name": "SM_CA_MW_PT_S06_Frame_Flange_LOD0_v001",
        "dimensions": (648.0, 620.0, 900.0),
        "unreal_triangles": 8592,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    "S06_Cue": {
        "name": "SM_CA_MW_PT_S06_Cue_RestrikeQuality_LOD0_v001",
        "dimensions": (54.5, 224.0, 178.0),
        "unreal_triangles": 3352,
        "slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_WorkedSteel",
            "CA_MW_CairnwellGreen", "CA_MW_StatusGreen",
            "CA_MW_TrainAAccent",
        ),
    },
    "Shared_PressSlide": {
        "name": "SM_CA_MW_PT_Shared_PressSlide_LOD0_v001",
        "dimensions": (500.0, 420.0, 87.0),
        "unreal_triangles": 216,
        "slots": ("CA_MW_WorkedSteel", "CA_MW_ServiceGrey"),
    },
    "Shared_MovingBolster": {
        "name": "SM_CA_MW_PT_Shared_MovingBolster_LOD0_v001",
        "dimensions": (520.0, 500.0, 50.0),
        "unreal_triangles": 1052,
        "slots": ("CA_MW_WorkedSteel", "CA_MW_ServiceGrey"),
    },
    "Shared_StageDieSet": {
        "name": "SM_CA_MW_PT_Shared_StageDieSet_LOD0_v001",
        "dimensions": (480.0, 360.0, 95.0),
        "unreal_triangles": 1064,
        "slots": (
            "CA_MW_WorkedSteel", "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
        ),
    },
}
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


def package_path(object_path_value: str) -> str:
    return object_path_value.rsplit(".", 1)[0]


def asset_path(asset) -> str:
    return str(asset.get_path_name()) if asset else "none"


def snapshot_content() -> dict:
    result = {}
    for path in sorted(CONTENT_ROOT.rglob("*.uasset")):
        result[str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")] = {
            "sha256": sha256(path), "mtime_ns": path.stat().st_mtime_ns,
        }
    return result


def texture_name(family: str, channel: str) -> str:
    return f"T_CA_MW_PT_{family}_{channel}"


def material_name(family: str) -> str:
    return f"MI_CA_MW_PT_{family}_v001"


def expected_material_path_for_slot(slot: str) -> str:
    if not slot.startswith("CA_MW_"):
        raise RuntimeError(f"unexpected semantic slot: {slot}")
    family = slot.removeprefix("CA_MW_")
    return object_path(MATERIAL_DESTINATION, material_name(family))


def audit_texture(texture, name: str, channel: str, failures: list[str]) -> dict:
    expected_srgb = channel == "BC"
    expected_compression = {
        "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
        "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
        "ORM": unreal.TextureCompressionSettings.TC_MASKS,
        "MASK": unreal.TextureCompressionSettings.TC_MASKS,
    }[channel]
    result = {"path": asset_path(texture)}
    if not texture or not isinstance(texture, unreal.Texture):
        failures.append(f"{name} does not resolve to a Texture")
        result["valid"] = False
        return result
    srgb = bool(texture.get_editor_property("srgb"))
    compression = texture.get_editor_property("compression_settings")
    flip_green = bool(texture.get_editor_property("flip_green_channel"))
    valid = (srgb == expected_srgb and compression == expected_compression
             and flip_green == (channel == "N"))
    if not valid:
        failures.append(
            f"{name} settings srgb={srgb} compression={compression} flip={flip_green}")
    result.update({
        "srgb": srgb, "compression": str(compression),
        "flip_green_channel": flip_green, "valid": valid,
    })
    return result


def audit() -> dict:
    failures: list[str] = []
    before = snapshot_content()
    if len(before) != 57:
        failures.append(f"expected 57 native StagePack uassets, found {len(before)}")

    expected_textures = {
        texture_name(family, channel): object_path(
            TEXTURE_DESTINATION, texture_name(family, channel))
        for family in FAMILIES for channel in CHANNELS
    }
    expected_meshes = {
        key: object_path(MESH_DESTINATION, spec["name"])
        for key, spec in MESHES.items()
    }
    expected_materials = {
        family: object_path(MATERIAL_DESTINATION, material_name(family))
        for family in FAMILIES
    }
    expected_packages = {
        *{package_path(path) for path in expected_textures.values()},
        *{package_path(path) for path in expected_meshes.values()},
        package_path(MASTER_PATH),
        *{package_path(path) for path in expected_materials.values()},
    }
    actual_packages = {
        package_path(str(path)) for path in unreal.EditorAssetLibrary.list_assets(
            DESTINATION, recursive=True, include_folder=False)
    }
    if actual_packages != expected_packages:
        failures.append("native StagePack package inventory differs from exact 57-package closure")

    texture_results = {}
    textures = {}
    for name, path in sorted(expected_textures.items()):
        texture = unreal.load_asset(path)
        textures[name] = texture
        texture_results[name] = audit_texture(texture, name, name.rsplit("_", 1)[1], failures)

    master = unreal.load_asset(MASTER_PATH)
    master_results = {"path": asset_path(master)}
    if not master or not isinstance(master, unreal.Material):
        failures.append("StagePack PBR master does not resolve to a Material")
    else:
        blend_mode = master.get_editor_property("blend_mode")
        master_results["blend_mode"] = str(blend_mode)
        master_results["blend_mode_name"] = getattr(blend_mode, "name", None)
        master_results["two_sided"] = bool(master.get_editor_property("two_sided"))
        # ``str(enum)`` includes the numeric value in UE 5.8 (for example
        # ``<BlendMode.BLEND_OPAQUE: 0>``), so inspect the enum name rather
        # than matching a presentation string.
        if master_results["blend_mode_name"] != "BLEND_OPAQUE":
            failures.append("StagePack master must remain opaque")
        if master_results["two_sided"]:
            failures.append("StagePack master must remain one-sided")
        defaults = {}
        for parameter, channel in TEXTURE_PARAMETERS.items():
            actual = unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(
                master, parameter)
            expected = expected_textures[texture_name("FoundryCharcoal", channel)]
            defaults[parameter] = asset_path(actual)
            if defaults[parameter] != expected:
                failures.append(f"master {parameter} drifted from FoundryCharcoal default")
        master_results["texture_defaults"] = defaults
        dust = float(unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(
            master, "RawDustStrength"))
        master_results["RawDustStrength"] = dust
        if abs(dust) > 0.0001:
            failures.append(f"master RawDustStrength={dust}, expected zero")
        expected_samplers = {
            "BaseColorMap": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
            "NormalMap": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
            "ORMMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
            "WearMaskMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        }
        samples = {
            str(node.get_editor_property("parameter_name")): node
            for node in unreal.MaterialEditingLibrary.get_material_expressions(master)
            if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D)
        }
        sampler_results = {}
        if set(samples) != set(expected_samplers):
            failures.append("StagePack master texture parameter graph drifted")
        else:
            for parameter, expected_sampler in expected_samplers.items():
                actual_sampler = samples[parameter].get_editor_property("sampler_type")
                sampler_results[parameter] = str(actual_sampler)
                if actual_sampler != expected_sampler:
                    failures.append(f"StagePack master sampler type drifted: {parameter}")
        master_results["samplers"] = sampler_results
        # The initial native material import addressed ComponentMask's unnamed
        # input as ``Input``.  UE silently left those nodes unwired; the
        # narrowly-scoped repair receipt records their correction.  Verify the
        # live graph here so a future import/rebind cannot regress to the
        # default material without this audit noticing.
        expected_mask_inputs = {320: "ORMMap", 400: "ORMMap", 480: "ORMMap",
                                600: "WearMaskMap"}
        masks = [node for node in unreal.MaterialEditingLibrary.get_material_expressions(master)
                 if isinstance(node, unreal.MaterialExpressionComponentMask)]
        by_y = {int(node.get_editor_property("material_expression_editor_y")): node
                for node in masks}
        mask_results = {}
        if len(masks) != 4 or set(by_y) != set(expected_mask_inputs):
            failures.append("StagePack master ComponentMask graph shape drifted")
        else:
            for y, parameter in sorted(expected_mask_inputs.items()):
                node = by_y[y]
                inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
                    master, node))
                source = inputs[0] if len(inputs) == 1 else None
                source_parameter = (str(source.get_editor_property("parameter_name"))
                                    if source and isinstance(
                                        source, unreal.MaterialExpressionTextureSampleParameter2D)
                                    else None)
                output = (str(unreal.MaterialEditingLibrary
                              .get_input_node_output_name_for_material_expression(node, source))
                          if source else None)
                mask_results[str(y)] = {"source_parameter": source_parameter,
                                        "output": output}
                if source_parameter != parameter or output != "RGB":
                    failures.append(
                        f"StagePack master ComponentMask y={y} is not wired to {parameter}.RGB")
        master_results["component_mask_inputs"] = mask_results

    material_results = {}
    for family, path in sorted(expected_materials.items()):
        material = unreal.load_asset(path)
        result = {"path": asset_path(material), "family": family}
        if not material or not isinstance(material, unreal.MaterialInstanceConstant):
            failures.append(f"{family} material does not resolve to a MaterialInstanceConstant")
            material_results[family] = result
            continue
        parent = asset_path(material.get_editor_property("parent"))
        result["parent"] = parent
        if parent != MASTER_PATH:
            failures.append(f"{family} parent drifted from StagePack master")
        parameters = {}
        for parameter, channel in TEXTURE_PARAMETERS.items():
            actual = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                material, parameter)
            expected = expected_textures[texture_name(family, channel)]
            parameters[parameter] = asset_path(actual)
            if parameters[parameter] != expected:
                failures.append(f"{family} {parameter} does not use its semantic map")
        dust = float(unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
            material, "RawDustStrength"))
        result["texture_parameters"] = parameters
        result["RawDustStrength"] = dust
        if abs(dust - FAMILY_DUST[family]) > 0.0001:
            failures.append(f"{family} raw dust value drifted")
        material_results[family] = result

    mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if mesh_editor is None or not hasattr(mesh_editor, "get_num_uv_channels"):
        failures.append("StaticMeshEditorSubsystem UV query is unavailable")
    mesh_results = {}
    for key, spec in MESHES.items():
        mesh = unreal.load_asset(expected_meshes[key])
        result = {"path": asset_path(mesh)}
        if not mesh or not isinstance(mesh, unreal.StaticMesh):
            failures.append(f"{key} does not resolve to a StaticMesh")
            mesh_results[key] = result
            continue
        bounds = mesh.get_bounding_box()
        size = bounds.max - bounds.min
        dimensions = (round(size.x, 3), round(size.y, 3), round(size.z, 3))
        triangles = int(mesh.get_num_triangles(0))
        slots = tuple(str(slot.material_slot_name) for slot in mesh.static_materials)
        material_paths = tuple(asset_path(
            slot.get_editor_property("material_interface")) for slot in mesh.static_materials)
        expected_material_paths = tuple(expected_material_path_for_slot(slot) for slot in spec["slots"])
        uv_channels = (int(mesh_editor.get_num_uv_channels(mesh, 0))
                       if mesh_editor is not None else None)
        simple_collision = (int(mesh_editor.get_simple_collision_count(mesh))
                            if mesh_editor is not None
                            and hasattr(mesh_editor, "get_simple_collision_count") else None)
        convex_collision = (int(mesh_editor.get_convex_collision_count(mesh))
                            if mesh_editor is not None
                            and hasattr(mesh_editor, "get_convex_collision_count") else None)
        result.update({
            "dimensions_cm": dimensions,
            "lod_count": int(mesh.get_num_lods()),
            "unreal_render_triangles": triangles,
            "uv_channels": uv_channels,
            "light_map_coordinate_index": int(mesh.get_editor_property("light_map_coordinate_index")),
            "light_map_resolution": int(mesh.get_editor_property("light_map_resolution")),
            "semantic_slots": slots,
            "default_materials": material_paths,
            "simple_collision_count": simple_collision,
            "convex_collision_count": convex_collision,
        })
        if any(abs(actual - expected) > 0.1
               for actual, expected in zip(dimensions, spec["dimensions"])):
            failures.append(f"{key} bounds drifted: {dimensions}")
        if triangles != spec["unreal_triangles"]:
            failures.append(f"{key} UE LOD0 triangles={triangles}, expected {spec['unreal_triangles']}")
        if result["lod_count"] != 1 or uv_channels is None or uv_channels < 2:
            failures.append(f"{key} LOD/UV closure drifted")
        if result["light_map_coordinate_index"] != 1 or result["light_map_resolution"] != 128:
            failures.append(f"{key} lightmap UV contract drifted")
        if slots != spec["slots"]:
            failures.append(f"{key} semantic slot order drifted")
        if material_paths != expected_material_paths:
            failures.append(f"{key} default mesh materials drifted from semantic MI closure")
        if simple_collision not in (0, None) or convex_collision not in (0, None):
            failures.append(f"{key} unexpectedly has imported collision")
        mesh_results[key] = result

    after = snapshot_content()
    if after != before:
        failures.append("read-only audit mutated native StagePack Content")
    return {
        "$schema": "lineboss/audit/onefactory/press/s03s06-stagepack-v003-native/v1",
        "generated_utc": now(),
        "write_scope": [str(RECEIPT)],
        "content_writes": [],
        "map_loaded_or_saved": [],
        "source_or_importer_rerun": False,
        "importer_sha256": sha256(IMPORTER),
        "native_package_count": len(actual_packages),
        "textures": texture_results,
        "master": master_results,
        "material_instances": material_results,
        "meshes": mesh_results,
        "source_topology_semantics": {
            "published_base_topology_triangles": 14652,
            "evaluated_fbx_payload_triangles": 46300,
            "unreal_lod0_render_triangles": 45532,
            "unreal_culled_degenerate_or_near_degenerate_triangles": 768,
            "source_runtimeprep_v001_export_triangle_field_is_accurate": False,
            "integration_status": "NATIVE_IMPORT_ACCEPTED_WITH_DOCUMENTED_SOURCE_TOPOLOGY_EXCEPTION",
            "required_source_followup": (
                "RuntimePrep v002 must record base, evaluated-FBX, and UE-native "
                "counts separately and declare/remove degenerates."),
        },
        "native_package_snapshot_before": before,
        "native_package_snapshot_after": after,
        "native_packages_unchanged": after == before,
        "failures": failures,
        "status": (
            "PASS__STAGEPACK_V003_CURRENT_NATIVE_CLOSURE__SOURCE_TOPOLOGY_EXCEPTION_RECORDED"
            if not failures else "FAIL__STAGEPACK_V003_CURRENT_NATIVE_CLOSURE"),
    }


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = audit()
        RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        if result["failures"]:
            raise RuntimeError("; ".join(result["failures"]))
        unreal.log("S03S06_STAGEPACK_V003_NATIVE_AUDIT_PASS")
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        failure = {
            "$schema": "lineboss/audit/onefactory/press/s03s06-stagepack-v003-native/v1",
            "generated_utc": now(),
            "status": "FAIL__STAGEPACK_V003_CURRENT_NATIVE_CLOSURE",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "write_scope": [str(RECEIPT)],
            "content_writes": [],
            "map_loaded_or_saved": [],
        }
        RECEIPT.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        unreal.log_error("S03S06_STAGEPACK_V003_NATIVE_AUDIT_FAIL: " + str(error))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
