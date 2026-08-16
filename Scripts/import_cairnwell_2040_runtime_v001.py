"""Incident-chained recovery-v009 UE 5.8 importer for approved Cairnwell v005.

This script is deliberately runnable only through the guarded lane runner after
the exact Meshy-derived v005 contract and complete project baseline have been
frozen.  It creates exactly eleven packages in a previously absent namespace,
bootstraps only immutable /Engine/Maps/Entry, never loads or saves a project map,
and preserves partial output on failure.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

import unreal


SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import cairnwell_2040_runtime_v001 as lane


PASS_STATUS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_FRESH_IMPORT__4_MESHES__"
    "12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE"
)
COMPRESSION_BY_NAME = lane.TEXTURE_COMPRESSION_BY_NAME


def texture_task(spec: dict):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(lane.PROJECT / spec["source"]["path"]),
        "destination_path": spec["package_path"].rsplit("/", 1)[0],
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
    })
    return task


def import_textures(baseline: dict) -> tuple[dict, dict]:
    keys = sorted(baseline["textures"])
    tasks = [texture_task(baseline["textures"][key]) for key in keys]
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    textures = {}
    evidence = {}
    for key, task in zip(keys, tasks):
        spec = baseline["textures"][key]
        imported = [str(value) for value in task.get_editor_property("imported_object_paths")]
        if imported != [spec["object_path"]]:
            lane.fail(f"fresh texture task result drift: {key}:{imported}")
        texture = lane.library.load_asset(spec["package_path"])
        if not isinstance(texture, unreal.Texture2D) or texture.get_path_name() != spec["object_path"]:
            lane.fail("fresh Texture2D/object identity drift: " + key)
        compression = COMPRESSION_BY_NAME.get(spec["compression"])
        if compression is None:
            lane.fail("unsupported frozen texture compression: " + spec["compression"])
        texture.set_editor_properties({
            "srgb": bool(spec["srgb"]),
            "compression_settings": compression,
            "flip_green_channel": bool(spec["flip_green_channel"]),
            "never_stream": False,
        })
        if not lane.library.save_loaded_asset(texture, only_if_is_dirty=False):
            lane.fail("configured texture save failed: " + key)
        textures[key] = texture
        measured_compression = texture.get_editor_property("compression_settings")
        evidence[key] = {
            "source": spec["source"],
            "object_path": texture.get_path_name(),
            "dimensions": [int(texture.blueprint_get_size_x()),
                           int(texture.blueprint_get_size_y())],
            "source_channels": int(spec["channels"]),
            "source_colorspace": spec["source_colorspace"],
            "srgb": bool(texture.get_editor_property("srgb")),
            "compression": lane.canonical_enum_name(
                measured_compression, lane.TEXTURE_COMPRESSION_BY_NAME,
                key + ":compression_settings"),
            "compression_runtime_repr": repr(measured_compression),
            "flip_green_channel": bool(texture.get_editor_property("flip_green_channel")),
            "channel_mapping": spec["channel_mapping"],
            "normal_convention": spec.get("normal_convention"),
        }
    return textures, evidence


def new_material(spec: dict):
    if lane.library.does_asset_exist(spec["package_path"]):
        lane.fail("fresh material destination already exists: " + spec["package_path"])
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        spec["asset_name"],
        spec["package_path"].rsplit("/", 1)[0],
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if not isinstance(material, unreal.Material) or material.get_path_name() != spec["object_path"]:
        lane.fail("fresh Material/object identity drift: " + spec["material_key"])
    material.set_editor_properties({
        "two_sided": False,
        "blend_mode": unreal.BlendMode.BLEND_OPAQUE,
        "material_domain": unreal.MaterialDomain.MD_SURFACE,
    })
    return material


def connect(material, expression, output: str, prop, label: str) -> None:
    if not unreal.MaterialEditingLibrary.connect_material_property(expression, output, prop):
        lane.fail("material graph connection failed: " + label)


def connect_nodes(source, output: str, target, input_name: str, label: str) -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(
            source, output, target, input_name):
        lane.fail("material expression connection failed: " + label)


def create_textured_material(spec: dict, textures: dict):
    material = new_material(spec)
    editing = unreal.MaterialEditingLibrary
    base = editing.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -760, -180)
    masks = editing.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -760, 90)
    normal = editing.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -760, 380)
    if base is None or masks is None or normal is None:
        lane.fail("textured material expression creation failed: " + spec["material_key"])
    base.set_editor_properties({
        "texture": textures["base_color"],
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    })
    masks.set_editor_properties({
        "texture": textures["metallic_roughness"],
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    })
    normal.set_editor_properties({
        "texture": textures["normal"],
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    })
    key = spec["material_key"]
    connect(material, base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR, key + ":base_color")
    connect(material, masks, spec["metallic_channel"],
            unreal.MaterialProperty.MP_METALLIC, key + ":metallic")
    connect(material, masks, spec["roughness_channel"],
            unreal.MaterialProperty.MP_ROUGHNESS, key + ":roughness")
    connect(material, normal, "RGB", unreal.MaterialProperty.MP_NORMAL, key + ":normal")
    editing.recompile_material(material)
    if not lane.library.save_loaded_asset(material, only_if_is_dirty=False):
        lane.fail("textured material save failed: " + key)
    return material


def create_textured_tint_material(spec: dict, textures: dict):
    """Build masked absolute-hue paint while retaining source tonal detail."""
    if (spec.get("parameter_name") != "VehiclePaintColour"
            or spec.get("parameter_output") != "RGB"
            or spec.get("paint_mask_target_input") != "Alpha"):
        lane.fail("body player-paint parameter/output/Alpha socket contract drift")
    material = new_material(spec)
    editing = unreal.MaterialEditingLibrary
    base = editing.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -900, -260)
    masks = editing.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -900, 260)
    normal = editing.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -900, 520)
    luminance_weights = editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -650, -360)
    luminance = editing.create_material_expression(
        material, unreal.MaterialExpressionDotProduct, -430, -350)
    normalization = editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -430, -250)
    normalized_luminance = editing.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -210, -330)
    detail_clamp = editing.create_material_expression(
        material, unreal.MaterialExpressionClamp, 10, -330)
    paint = editing.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -210, -100)
    tinted_base = editing.create_material_expression(
        material, unreal.MaterialExpressionMultiply, 230, -160)
    masked_tint = editing.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 470, -220)
    if any(node is None for node in (
            base, masks, normal, luminance_weights, luminance, normalization,
            normalized_luminance, detail_clamp, paint, tinted_base, masked_tint)):
        lane.fail("body masked-tint material expression creation failed")
    base.set_editor_properties({
        "texture": textures["base_color"],
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    })
    masks.set_editor_properties({
        "texture": textures["metallic_roughness"],
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    })
    normal.set_editor_properties({
        "texture": textures["normal"],
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    })
    weights = [float(value) for value in spec["detail_luminance_weights"]]
    luminance_weights.set_editor_property(
        "constant", unreal.LinearColor(*weights, 1.0))
    normalization.set_editor_property("r", float(spec["detail_normalization"]))
    detail_clamp.set_editor_properties({
        "min_default": float(spec["detail_clamp_min"]),
        "max_default": float(spec["detail_clamp_max"]),
    })
    colour = [float(value) for value in spec["default_paint_colour_linear"]]
    paint.set_editor_properties({
        "parameter_name": "VehiclePaintColour",
        "default_value": unreal.LinearColor(*colour, 1.0),
    })
    connect_nodes(base, "RGB", luminance, "A", "body:base_to_luminance")
    connect_nodes(luminance_weights, "", luminance, "B", "body:luminance_weights")
    connect_nodes(luminance, "", normalized_luminance, "A", "body:luminance_to_normalize")
    connect_nodes(normalization, "", normalized_luminance, "B", "body:detail_normalization")
    # UE 5.8 shortens the semantic Clamp `Input` pin to NAME_None in
    # MaterialEditingLibrary, so its first input must be addressed by "".
    connect_nodes(normalized_luminance, "", detail_clamp, "", "body:normalized_detail_to_clamp")
    connect_nodes(paint, spec["parameter_output"], tinted_base, "A",
                  "body:paint_parameter_to_absolute_hue")
    connect_nodes(detail_clamp, "", tinted_base, "B",
                  "body:clamped_luminance_to_paint_detail")
    connect_nodes(base, "RGB", masked_tint, "A", "body:untinted_base_to_lerp")
    connect_nodes(tinted_base, "", masked_tint, "B", "body:tinted_base_to_lerp")
    connect_nodes(
        masks, spec["paint_mask_channel"], masked_tint,
        spec["paint_mask_target_input"], "body:paint_mask_to_lerp")
    connect(material, masked_tint, "", unreal.MaterialProperty.MP_BASE_COLOR,
            "body:masked_tint_base_color")
    connect(material, masks, spec["metallic_channel"],
            unreal.MaterialProperty.MP_METALLIC, "body:metallic")
    connect(material, masks, spec["roughness_channel"],
            unreal.MaterialProperty.MP_ROUGHNESS, "body:roughness")
    connect(material, normal, "RGB", unreal.MaterialProperty.MP_NORMAL, "body:normal")
    editing.recompile_material(material)
    if not lane.library.save_loaded_asset(material, only_if_is_dirty=False):
        lane.fail("body masked-tint material save failed")
    return material


def create_solid_material(spec: dict):
    material = new_material(spec)
    editing = unreal.MaterialEditingLibrary
    base = editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -560, -120)
    metallic = editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -560, 80)
    roughness = editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -560, 240)
    if base is None or metallic is None or roughness is None:
        lane.fail("solid material expression creation failed: " + spec["material_key"])
    base.set_editor_property(
        "constant", unreal.LinearColor(*[float(value) for value in spec["base_color_linear"]], 1.0))
    metallic.set_editor_property("r", float(spec["metallic"]))
    roughness.set_editor_property("r", float(spec["roughness"]))
    key = spec["material_key"]
    connect(material, base, "", unreal.MaterialProperty.MP_BASE_COLOR, key + ":base_color")
    connect(material, metallic, "", unreal.MaterialProperty.MP_METALLIC, key + ":metallic")
    connect(material, roughness, "", unreal.MaterialProperty.MP_ROUGHNESS, key + ":roughness")
    editing.recompile_material(material)
    if not lane.library.save_loaded_asset(material, only_if_is_dirty=False):
        lane.fail("solid material save failed: " + key)
    return material


def create_materials(baseline: dict, textures: dict) -> tuple[dict, dict]:
    materials = {}
    evidence = {}
    for key, spec in sorted(baseline["materials"].items()):
        if spec["recipe"] == "textured_tint_pbr":
            material = create_textured_tint_material(spec, textures)
        elif spec["recipe"] == "textured_pbr":
            material = create_textured_material(spec, textures)
        else:
            material = create_solid_material(spec)
        materials[spec["object_path"]] = material
        evidence[key] = {
            "object_path": material.get_path_name(),
            "recipe": spec["recipe"],
            "slot_name": spec["slot_name"],
            "texture_object_paths": spec["texture_object_paths"],
            "parameter_name": spec.get("parameter_name"),
            "paint_mask_texture_semantic": spec.get("paint_mask_texture_semantic"),
            "paint_mask_channel": spec.get("paint_mask_channel"),
            "paint_mask_target_input": spec.get("paint_mask_target_input"),
            "tint_graph_topology": spec.get("tint_graph_topology"),
            "detail_luminance_weights": spec.get("detail_luminance_weights"),
            "detail_normalization": spec.get("detail_normalization"),
            "detail_clamp": [spec.get("detail_clamp_min"), spec.get("detail_clamp_max")],
        }
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    return materials, evidence


def mesh_task(spec: dict):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(lane.PROJECT / spec["lods"][0]["source"]["path"]),
        "destination_path": spec["package_path"].rsplit("/", 1)[0],
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
        "factory": unreal.FbxFactory(),
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "import_animations": False,
        "automated_import_should_detect_type": False,
        "create_physics_asset": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static = options.get_editor_property("static_mesh_import_data")
    static.set_editor_properties({
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "combine_meshes": True,
        "build_nanite": False,
    })
    options.set_editor_property("static_mesh_import_data", static)
    task.set_editor_property("options", options)
    return task


def import_lod0_meshes(baseline: dict) -> dict:
    roles = sorted(baseline["modules"])
    tasks = [mesh_task(baseline["modules"][role]) for role in roles]
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    meshes = {}
    for role, task in zip(roles, tasks):
        spec = baseline["modules"][role]
        imported = [str(value) for value in task.get_editor_property("imported_object_paths")]
        if imported != [spec["object_path"]]:
            lane.fail(f"fresh LOD0 task result drift: {role}:{imported}")
        mesh = lane.library.load_asset(spec["package_path"])
        if (not isinstance(mesh, unreal.StaticMesh)
                or mesh.get_path_name() != spec["object_path"]
                or int(mesh.get_num_lods()) != 1):
            lane.fail("fresh LOD0 StaticMesh/type/count drift: " + role)
        meshes[role] = mesh
    return meshes


def append_custom_lods(meshes: dict, baseline: dict, subsystem) -> dict:
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
    evidence = {
        "name": lane.INTERCHANGE_FBX_CVAR,
        "previous_value": previous,
        "disabled_value": None,
        "restored_value": None,
        "custom_lods_requested": 8,
        "custom_lods_imported": [],
        "restore_attempted_in_finally": False,
        "set_false_only_around_custom_lod_imports": True,
    }
    if previous not in (0, 1):
        lane.fail("unexpected Interchange FBX feature-flag value: " + str(previous))
    caught = None
    try:
        unreal.SystemLibrary.execute_console_command(None, lane.INTERCHANGE_FBX_CVAR + " 0")
        evidence["disabled_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
        if evidence["disabled_value"] != 0:
            lane.fail("could not activate the legacy custom-LOD importer")
        for role in sorted(meshes):
            for lod_index in (1, 2):
                source = lane.PROJECT / baseline["modules"][role]["lods"][lod_index]["source"]["path"]
                imported_lod_index = int(
                    subsystem.import_lod(meshes[role], lod_index, str(source)))
                if imported_lod_index != lod_index:
                    lane.fail(f"authored custom LOD append failed: {role}:LOD{lod_index}")
                evidence["custom_lods_imported"].append({
                    "role": role,
                    "lod": lod_index,
                    "source": lane.relative(source),
                    "source_sha256": lane.sha256(source),
                })
    except Exception as error:
        caught = error
    finally:
        evidence["restore_attempted_in_finally"] = True
        unreal.SystemLibrary.execute_console_command(
            None, f"{lane.INTERCHANGE_FBX_CVAR} {previous}")
        evidence["restored_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
    if evidence["restored_value"] != previous:
        lane.fail("Interchange FBX feature flag restoration drift: " + repr(evidence))
    if caught is not None:
        raise caught
    if len(evidence["custom_lods_imported"]) != 8:
        lane.fail("authored custom-LOD append count drift")
    return evidence


def normalize_gameplay_material_slot(role: str, spec: dict, mesh, baseline: dict) -> dict:
    rule = baseline["_recovery"]["slot_normalization"][role]
    static_materials = list(mesh.get_editor_property("static_materials"))
    actual_slots = lane.slot_names(mesh)
    imported_slots = lane.imported_slot_names(mesh)
    expected_imported = [rule["ue_imported_material_slot_name"]]
    expected_canonical = [rule["canonical_material_slot_name"]]
    if (len(static_materials) != int(rule["required_static_material_count"])
            or actual_slots != expected_imported
            or imported_slots != expected_imported):
        lane.fail(
            "exact source-sanitized material-slot identity/count drift: "
            + role + repr({"slots": actual_slots, "imported": imported_slots}))
    changed = bool(rule["normalize_gameplay_material_slot_name"])
    if changed:
        static_materials[0].set_editor_property(
            "material_slot_name", rule["canonical_material_slot_name"])
        mesh.set_editor_property("static_materials", static_materials)
    final_slots = lane.slot_names(mesh)
    final_imported = lane.imported_slot_names(mesh)
    if final_slots != expected_canonical or final_imported != expected_imported:
        lane.fail("canonical/imported material-slot normalization drift: " + role)
    return {
        "role": role,
        "source_fbx_material_name": rule["source_fbx_material_name"],
        "ue_imported_before": actual_slots,
        "imported_identity_after": final_imported,
        "canonical_gameplay_after": final_slots,
        "normalization_applied": changed,
        "source_occurrence_count_by_lod": rule["source_occurrence_count_by_lod"],
    }


def configure_mesh(role: str, spec: dict, mesh, materials: dict,
                   subsystem, baseline: dict) -> dict:
    if int(mesh.get_num_lods()) != 3:
        lane.fail("expected exactly three authored LOD source models: " + role)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    subsystem.set_nanite_settings(mesh, nanite, apply_changes=True)
    if (int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)) != 0
            or int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh)) != 0):
        lane.fail("fresh moving-vehicle module unexpectedly contains collision: " + role)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        lane.fail("BodySetup missing: " + role)
    body.set_editor_property(
        "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    mesh.set_editor_property("has_navigation_data", False)
    normalization = normalize_gameplay_material_slot(role, spec, mesh, baseline)
    slots = lane.slot_names(mesh)
    for index, slot in enumerate(slots):
        object_path = spec["material_bindings"][slot]
        material = materials.get(object_path)
        if not isinstance(material, unreal.MaterialInterface):
            lane.fail(f"declared material binding is unavailable: {role}:{slot}:{object_path}")
        mesh.set_material(index, material)
    if not lane.library.save_loaded_asset(mesh, only_if_is_dirty=False):
        lane.fail("configured mesh save failed: " + role)
    return normalization


def persist_manual_screens(meshes: dict, baseline: dict, subsystem) -> dict:
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    wanted = [float(value) for value in baseline["import_contract"]["lod_screen_sizes"]]
    rounded = [round(value, 6) for value in wanted]
    evidence = {role: [] for role in meshes}
    for pass_index in (1, 2):
        if pass_index == 2:
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        for role in sorted(meshes):
            mesh = meshes[role]
            if not subsystem.set_lod_screen_sizes(mesh, wanted):
                lane.fail(f"manual screen-size pass {pass_index} failed: {role}")
            readback = [round(float(value), 6)
                        for value in subsystem.get_lod_screen_sizes(mesh)]
            automatic = bool(mesh.is_lod_screen_size_auto_computed())
            if readback != rounded or automatic:
                lane.fail(
                    f"manual screen-size pass {pass_index} drift: {role}:{readback}:{automatic}")
            if not lane.library.save_loaded_asset(mesh, only_if_is_dirty=False):
                lane.fail(f"manual screen-size pass {pass_index} save failed: {role}")
            post_save = [round(float(value), 6)
                         for value in subsystem.get_lod_screen_sizes(mesh)]
            post_save_automatic = bool(mesh.is_lod_screen_size_auto_computed())
            if post_save != rounded or post_save_automatic:
                lane.fail(
                    f"manual screen-size pass {pass_index} post-save drift: "
                    f"{role}:{post_save}:{post_save_automatic}")
            evidence[role].append({
                "pass": pass_index,
                "readback": readback,
                "auto_compute": automatic,
                "post_save_readback": post_save,
                "post_save_auto_compute": post_save_automatic,
            })
    return evidence


def main() -> None:
    root = lane.run_root()
    receipt = root / lane.IMPORT_RECEIPT
    failure = root / lane.IMPORT_FAILURE
    record = {
        "$schema": (
            "lineboss/audit/cairnwell-2040-runtime-v001/"
            "recovery-v009/unreal-import/v9"),
        "generated_utc": lane.now(),
        "process_id": os.getpid(),
        "destination_namespace": lane.DEST,
        "writes_authorized": [str(lane.DEST_DISK), str(root)],
        "editor_bootstrap_world": None,
        "project_maps_loaded_or_saved": [],
        "replace_reimport_delete_operations": [],
        "runtime_binding_or_promotion_changes": [],
    }
    source_before = protected_before = prepared_lane_before = None
    quarantine_receipt = None
    try:
        record["editor_bootstrap_world"] = lane.require_engine_entry_bootstrap_world()
        if receipt.exists() or failure.exists():
            lane.fail("current run already contains an import result")
        baseline = lane.load_baseline()
        quarantine_receipt = lane.require_quarantine_receipt(
            baseline["_recovery"], baseline["_recovery_contract_sha256"])
        if lane.prior_results():
            lane.fail("recovery v009 run already contains a PASS or FAIL result")
        if lane.DEST_DISK.exists() or lane.library.does_directory_exist(lane.DEST):
            lane.fail("fresh destination already exists; overwrite/reimport forbidden")
        if lane.library.list_assets(lane.DEST, recursive=True, include_folder=False):
            lane.fail("asset registry already exposes the fresh destination")
        for package in baseline["destination"]["expected_package_paths"]:
            if lane.library.does_asset_exist(package):
                lane.fail("fresh object package already exists: " + package)

        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline)
        prepared_lane_before = lane.verify_lane(baseline)

        textures, texture_creation = import_textures(baseline)
        materials, material_creation = create_materials(baseline, textures)
        meshes = import_lod0_meshes(baseline)
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None or not hasattr(subsystem, "import_lod"):
            lane.fail("UE5.8 StaticMeshEditorSubsystem/custom-LOD API unavailable")
        cvar = append_custom_lods(meshes, baseline, subsystem)
        slot_normalization = {}
        for role, spec in sorted(baseline["modules"].items()):
            slot_normalization[role] = configure_mesh(
                role, spec, meshes[role], materials, subsystem, baseline)
        screens = persist_manual_screens(meshes, baseline, subsystem)

        # Same-process AssetRegistry dependency rows can lag newly saved packages;
        # graph/binding closure is checked here and persisted registry closure is
        # reserved for the distinct fresh process.
        measured = lane.validate_all_assets(
            baseline, require_persisted_dependencies=False)
        registry = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)
        }
        expected_registry = set(baseline["destination"]["expected_package_paths"])
        if registry != expected_registry:
            lane.fail("exact eleven-package asset-registry closure drift: " + repr(sorted(registry)))
        disk = lane.namespace_inventory()
        expected_disk = {
            spec["disk_path"]
            for collection in (baseline["modules"], baseline["textures"], baseline["materials"])
            for spec in collection.values()
        }
        if set(disk) != expected_disk:
            lane.fail("exact eleven-package disk inventory drift: " + repr(sorted(disk)))
        packages = lane.package_hashes(baseline)

        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline)
        prepared_lane_after = lane.verify_lane(baseline)
        if (source_after != source_before or protected_after != protected_before
                or prepared_lane_after != prepared_lane_before):
            lane.fail("approved sources, protected project, or prepared lane changed during import")
        if int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR)) != int(
                cvar["previous_value"]):
            lane.fail("Interchange FBX feature flag changed after guarded restoration")

        record.update({
            "status": PASS_STATUS,
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "contract_sha256": baseline["_contract_sha256"],
            "baseline_sha256": baseline["_baseline_sha256"],
            "recovery_contract_sha256": baseline["_recovery_contract_sha256"],
            "v001_failed_run_id": lane.EXPECTED_V001_FAILED_RUN_ID,
            "v001_import_failure_sha256": lane.EXPECTED_V001_IMPORT_FAILURE_SHA256,
            "v002_failed_run_id": lane.EXPECTED_V002_FAILED_RUN_ID,
            "v002_import_failure_sha256": lane.EXPECTED_V002_IMPORT_FAILURE_SHA256,
            "v003_failed_run_id": lane.EXPECTED_V003_FAILED_RUN_ID,
            "v003_import_failure_sha256": lane.EXPECTED_V003_IMPORT_FAILURE_SHA256,
            "v004_failed_run_id": lane.EXPECTED_V004_FAILED_RUN_ID,
            "v004_import_failure_sha256": lane.EXPECTED_V004_IMPORT_FAILURE_SHA256,
            "v005_failed_run_id": lane.EXPECTED_V005_FAILED_RUN_ID,
            "v005_import_failure_sha256": lane.EXPECTED_V005_IMPORT_FAILURE_SHA256,
            "v006_failed_run_id": lane.EXPECTED_V006_FAILED_RUN_ID,
            "v006_import_failure_sha256": lane.EXPECTED_V006_IMPORT_FAILURE_SHA256,
            "incident_chain_sha256": baseline["_recovery"]["incident_chain"]["binding_sha256"],
            "quarantine_receipt": quarantine_receipt,
            "source_before": source_before,
            "source_after": source_after,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "prepared_lane_before": prepared_lane_before,
            "prepared_lane_after": prepared_lane_after,
            "texture_creation": texture_creation,
            "material_creation": material_creation,
            "interchange_fbx_legacy_custom_lod_guard": cvar,
            "manual_screen_size_persistence": screens,
            "deterministic_material_slot_normalization": slot_normalization,
            "assets": measured,
            "asset_registry_packages": sorted(registry, key=str.casefold),
            "namespace_disk_files": disk,
            "package_sha256": packages,
            "mesh_count": 4,
            "authored_lod_count": 12,
            "source_fbx_count": 12,
            "texture_count": 3,
            "material_count": 4,
            "package_count": 11,
            "nanite_collision_navigation_off_verified": True,
            "strict_lod_uv_bounds_pivot_material_gates_verified": True,
            "exact_texture_material_dependency_closure_verified": True,
            "fresh_process_validator_required": True,
            "failures": [],
            "automatic_cleanup": (
                "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW"),
        })
        lane.write_json(receipt, record)
        unreal.log("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_IMPORT_PASS")
        print(json.dumps(record, indent=2))
    except Exception as error:
        record.update({
            "status": (
                "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_"
                "RECOVERY_V009_UNREAL_IMPORT"),
            "error": str(error),
            "traceback": traceback.format_exc(),
            "source_before": source_before,
            "protected_before": protected_before,
            "prepared_lane_before": prepared_lane_before,
            "v001_failed_run_id": lane.EXPECTED_V001_FAILED_RUN_ID,
            "v001_import_failure_sha256": lane.EXPECTED_V001_IMPORT_FAILURE_SHA256,
            "v002_failed_run_id": lane.EXPECTED_V002_FAILED_RUN_ID,
            "v002_import_failure_sha256": lane.EXPECTED_V002_IMPORT_FAILURE_SHA256,
            "v003_failed_run_id": lane.EXPECTED_V003_FAILED_RUN_ID,
            "v003_import_failure_sha256": lane.EXPECTED_V003_IMPORT_FAILURE_SHA256,
            "v004_failed_run_id": lane.EXPECTED_V004_FAILED_RUN_ID,
            "v004_import_failure_sha256": lane.EXPECTED_V004_IMPORT_FAILURE_SHA256,
            "v005_failed_run_id": lane.EXPECTED_V005_FAILED_RUN_ID,
            "v005_import_failure_sha256": lane.EXPECTED_V005_IMPORT_FAILURE_SHA256,
            "v006_failed_run_id": lane.EXPECTED_V006_FAILED_RUN_ID,
            "v006_import_failure_sha256": lane.EXPECTED_V006_IMPORT_FAILURE_SHA256,
            "incident_chain_sha256": (
                baseline["_recovery"]["incident_chain"]["binding_sha256"]
                if "baseline" in locals() else None),
            "quarantine_receipt": quarantine_receipt,
            "namespace_files_preserved_for_recovery": lane.namespace_inventory(),
            "automatic_cleanup": (
                "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW"),
            "recovery": (
                "Archive this run and all six prior quarantines; do not rerun "
                "recovery v009 or delete/replace packages implicitly."),
        })
        lane.write_json(failure, record)
        unreal.log_error("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_IMPORT_FAIL: " + str(error))
        print(json.dumps(record, indent=2))
        raise


if __name__ == "__main__":
    main()
