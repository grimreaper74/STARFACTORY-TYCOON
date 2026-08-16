"""Build the isolated PR-004 v020 reusable robot candidate.

The accepted v016 reusable composition and all source meshes remain untouched.
Every mesh used by the reusable robot/tool set is duplicated before UE 5.8
Geometry Script cleanup and candidate simple-collision generation.  Only
semantic CastIron material slots receive the lightweight Surface Forge-derived
Cairnwell-green paint material.  This script never promotes the candidate.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
IMPORT_PATH = ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json"
SOURCE_PATH = ROOT / "Saved/Audits/pr004_robot_candidate_v002_source.json"
AUDIT_PATH = ROOT / "Saved/Audits/press_shop_pr004_surfaceforge_robot_candidate_v020.json"

ACCEPTED_INTEGRATION_BASELINE = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotCandidate_v016"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SurfaceForgeRobotCandidate_v020"
SOURCE_ROBOT_LABEL = "LB_INT_PR004_BP_ModularRobot_400kg_v002"
DEST_ROBOT_LABEL = "LB_INT_PR004_BP_ModularRobot_400kg_v020"

ASSET_ROOT = "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020"
MESH_ROOT = ASSET_ROOT + "/Meshes"
MATERIAL_ROOT = ASSET_ROOT + "/Materials"
TOOL_ROOT = ASSET_ROOT + "/Tools"
BRAND_ROOT = "/Game/LineBoss/Brand/Cairnwell/Candidate_v020/RobotPlate"

SURFACE_BASE = "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Base_Color_Metal_Paint_Chips.T_Base_Color_Metal_Paint_Chips"
SURFACE_NORMAL = "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Normal_Metal_Paint_Chips.T_Normal_Metal_Paint_Chips"
SURFACE_ORD = "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_ORD_Metal_Paint_Chips.T_ORD_Metal_Paint_Chips"
SOURCE_PLATE_TEXTURE = "/Game/LineBoss/Brand/Cairnwell/Candidate_v005/RobotPlate/T_Cairnwell_PR004_RobotPlate_v001"

IMPORT = json.loads(IMPORT_PATH.read_text(encoding="utf-8"))
SOURCE = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
SOURCE_MODULES = {row["id"]: row for row in SOURCE["modules"]}
IMPORT_MODULES = {
    row["module_id"]: row for row in IMPORT["imported_assets"] if row["family"] == "robot_v002"
}

lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
bp_lib = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_lib = unreal.SubobjectDataBlueprintFunctionLibrary


CORE_COMPONENTS = [
    ("base", "BasePedestal", None),
    ("j1", "J1_BaseYaw", "base"),
    ("j2", "J2_Shoulder", "j1"),
    ("j3", "J3_Elbow", "j2"),
    ("j4", "J4_WristRoll", "j3"),
    ("j5", "J5_WristPitch", "j4"),
    ("j6", "J6_ToolRoll", "j5"),
    ("changer_body", "QuickChangerBody", "j6"),
    ("changer_lock", "QuickChangerLock", "changer_body"),
    ("dress_lower", "DressPackLower", "j1"),
    ("dress_upper", "DressPackUpper", "j2"),
    ("dress_wrist", "DressPackWrist", "j4"),
]

TOOL_DEFINITIONS = [
    (
        "BandCutterCapture",
        "BP_LB_RobotTool_BandCutterCapture_v020",
        "band_tool",
        [
            ("band_left_capture", "LeftCaptureJaw"),
            ("band_right_capture", "RightCaptureJaw"),
            ("band_cutter", "BandCutter"),
            ("band_roll_left", "LeftWithdrawalRoll"),
            ("band_roll_right", "RightWithdrawalRoll"),
        ],
        {
            "band_left_capture": (45.0, -28.0, 0.0),
            "band_right_capture": (45.0, 28.0, 0.0),
            "band_cutter": (60.0, 0.0, 0.0),
            "band_roll_left": (45.0, -28.0, -15.0),
            "band_roll_right": (45.0, 28.0, -15.0),
        },
    ),
    (
        "WrapPeelerVacuum",
        "BP_LB_RobotTool_WrapPeelerVacuum_v020",
        "wrap_tool",
        [("wrap_vacuum_carrier", "VacuumCarrier"), ("wrap_peel_roll", "PeelRoll")],
        {},
    ),
    (
        "EdgeProtectorGripper",
        "BP_LB_RobotTool_EdgeProtectorGripper_v020",
        "edge_tool",
        [("edge_left_jaw", "LeftJaw"), ("edge_right_jaw", "RightJaw")],
        {},
    ),
    (
        "LabelRFIDInspection",
        "BP_LB_RobotTool_LabelRFIDInspection_v020",
        "inspection_tool",
        [("inspection_bore_camera", "BoreCamera"), ("inspection_shutter", "CameraShutter")],
        {},
    ),
]


def expression(material, klass, x, y):
    return mel.create_material_expression(material, klass, x, y)


def require_asset(path, expected_type=None):
    asset = lib.load_asset(path)
    if asset is None or (expected_type is not None and not isinstance(asset, expected_type)):
        raise RuntimeError(f"Missing required asset: {path}")
    return asset


def package_path(object_path):
    return object_path.split(".", 1)[0]


def asset_name(object_path):
    return package_path(object_path).rsplit("/", 1)[-1]


def create_clean_material(name, folder):
    path = f"{folder}/{name}"
    if lib.does_asset_exist(path):
        raise RuntimeError(f"Refusing to overwrite preserved candidate material {path}")
    material = asset_tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create material {path}")
    return material


def build_surface_material():
    base_texture = require_asset(SURFACE_BASE, unreal.Texture2D)
    normal_texture = require_asset(SURFACE_NORMAL, unreal.Texture2D)
    ord_texture = require_asset(SURFACE_ORD, unreal.Texture2D)
    material = create_clean_material("M_LB_Robot_SurfaceForgePaint_Master_v020", MATERIAL_ROOT)
    material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})

    uv = expression(material, unreal.MaterialExpressionTextureCoordinate, -1260, -40)
    scale = expression(material, unreal.MaterialExpressionScalarParameter, -1260, 80)
    scale.set_editor_properties({"parameter_name": "TextureScale", "default_value": 2.6})
    scaled_uv = expression(material, unreal.MaterialExpressionMultiply, -1040, -20)
    mel.connect_material_expressions(uv, "", scaled_uv, "A")
    mel.connect_material_expressions(scale, "", scaled_uv, "B")

    base = expression(material, unreal.MaterialExpressionTextureSample, -820, -220)
    base.set_editor_properties({"texture": base_texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
    mel.connect_material_expressions(scaled_uv, "", base, "UVs")
    channel_delta = expression(material, unreal.MaterialExpressionSubtract, -600, -230)
    mel.connect_material_expressions(base, "R", channel_delta, "A")
    mel.connect_material_expressions(base, "B", channel_delta, "B")
    contrast = expression(material, unreal.MaterialExpressionScalarParameter, -600, -100)
    contrast.set_editor_properties({"parameter_name": "PaintMaskContrast", "default_value": 3.2})
    amplified = expression(material, unreal.MaterialExpressionMultiply, -390, -190)
    mel.connect_material_expressions(channel_delta, "", amplified, "A")
    mel.connect_material_expressions(contrast, "", amplified, "B")
    coverage = expression(material, unreal.MaterialExpressionScalarParameter, -390, -70)
    coverage.set_editor_properties({"parameter_name": "PaintCoverageBias", "default_value": 0.72})
    biased = expression(material, unreal.MaterialExpressionAdd, -180, -150)
    mel.connect_material_expressions(amplified, "", biased, "A")
    mel.connect_material_expressions(coverage, "", biased, "B")
    mask = expression(material, unreal.MaterialExpressionSaturate, 30, -150)
    mel.connect_material_expressions(biased, "", mask, "")

    exposed = expression(material, unreal.MaterialExpressionVectorParameter, -190, -390)
    exposed.set_editor_properties({
        "parameter_name": "ExposedMetalColour",
        "default_value": unreal.LinearColor(0.055, 0.065, 0.075, 1.0),
    })
    paint = expression(material, unreal.MaterialExpressionVectorParameter, -190, -300)
    paint.set_editor_properties({
        "parameter_name": "PaintColour",
        "default_value": unreal.LinearColor(0.025, 0.20, 0.12, 1.0),
    })
    colour = expression(material, unreal.MaterialExpressionLinearInterpolate, 250, -260)
    mel.connect_material_expressions(exposed, "", colour, "A")
    mel.connect_material_expressions(paint, "", colour, "B")
    mel.connect_material_expressions(mask, "", colour, "Alpha")
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)

    normal = expression(material, unreal.MaterialExpressionTextureSample, -820, 160)
    normal.set_editor_properties({"texture": normal_texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL})
    mel.connect_material_expressions(scaled_uv, "", normal, "UVs")
    flat = expression(material, unreal.MaterialExpressionConstant3Vector, -600, 300)
    flat.set_editor_property("constant", unreal.LinearColor(0.5, 0.5, 1.0, 1.0))
    normal_strength = expression(material, unreal.MaterialExpressionScalarParameter, -600, 400)
    normal_strength.set_editor_properties({"parameter_name": "NormalStrength", "default_value": 0.24})
    normal_blend = expression(material, unreal.MaterialExpressionLinearInterpolate, -160, 250)
    mel.connect_material_expressions(flat, "", normal_blend, "A")
    mel.connect_material_expressions(normal, "RGB", normal_blend, "B")
    mel.connect_material_expressions(normal_strength, "", normal_blend, "Alpha")
    mel.connect_material_property(normal_blend, "", unreal.MaterialProperty.MP_NORMAL)

    ord_sample = expression(material, unreal.MaterialExpressionTextureSample, -820, 560)
    ord_sample.set_editor_properties({"texture": ord_texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR})
    mel.connect_material_expressions(scaled_uv, "", ord_sample, "UVs")
    mel.connect_material_property(ord_sample, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    base_roughness = expression(material, unreal.MaterialExpressionScalarParameter, -580, 650)
    base_roughness.set_editor_properties({"parameter_name": "BaseRoughness", "default_value": 0.58})
    roughness_influence = expression(material, unreal.MaterialExpressionScalarParameter, -580, 750)
    roughness_influence.set_editor_properties({"parameter_name": "RoughnessVariation", "default_value": 0.34})
    roughness = expression(material, unreal.MaterialExpressionLinearInterpolate, -160, 620)
    mel.connect_material_expressions(base_roughness, "", roughness, "A")
    mel.connect_material_expressions(ord_sample, "G", roughness, "B")
    mel.connect_material_expressions(roughness_influence, "", roughness, "Alpha")
    mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

    inverse_mask = expression(material, unreal.MaterialExpressionOneMinus, 250, -60)
    mel.connect_material_expressions(mask, "", inverse_mask, "Input")
    exposed_metallic = expression(material, unreal.MaterialExpressionScalarParameter, 250, 50)
    exposed_metallic.set_editor_properties({"parameter_name": "ExposedMetallic", "default_value": 0.72})
    metallic = expression(material, unreal.MaterialExpressionMultiply, 470, -30)
    mel.connect_material_expressions(inverse_mask, "", metallic, "A")
    mel.connect_material_expressions(exposed_metallic, "", metallic, "B")
    mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)

    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)

    instance_name = "MI_LB_Robot_CairnwellGreen_Aged_v020"
    instance = asset_tools.create_asset(
        instance_name,
        MATERIAL_ROOT,
        unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew(),
    )
    if instance is None:
        raise RuntimeError("Could not create Surface Forge robot material instance")
    instance.set_editor_property("parent", material)
    mel.set_material_instance_vector_parameter_value(
        instance, "PaintColour", unreal.LinearColor(0.025, 0.20, 0.12, 1.0)
    )
    mel.set_material_instance_vector_parameter_value(
        instance, "ExposedMetalColour", unreal.LinearColor(0.050, 0.060, 0.070, 1.0)
    )
    for name, value in (
        ("TextureScale", 2.6),
        ("PaintMaskContrast", 3.2),
        ("PaintCoverageBias", 0.72),
        ("NormalStrength", 0.24),
        ("BaseRoughness", 0.58),
        ("RoughnessVariation", 0.34),
        ("ExposedMetallic", 0.72),
    ):
        mel.set_material_instance_scalar_parameter_value(instance, name, value)
    mel.update_material_instance(instance)
    lib.save_loaded_asset(instance, only_if_is_dirty=False)
    return material, instance


def build_plate_materials():
    source_texture = require_asset(SOURCE_PLATE_TEXTURE, unreal.Texture2D)
    texture_path = BRAND_ROOT + "/T_Cairnwell_PR004_RobotPlate_v020"
    if lib.does_asset_exist(texture_path):
        raise RuntimeError(f"Refusing to overwrite preserved candidate texture {texture_path}")
    if not lib.duplicate_asset(source_texture.get_path_name(), texture_path):
        raise RuntimeError("Could not duplicate deterministic Cairnwell plate texture")
    texture = require_asset(texture_path, unreal.Texture2D)
    texture.set_editor_properties({
        "srgb": True,
        "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
        "mip_gen_settings": unreal.TextureMipGenSettings.TMGS_SHARPEN2,
        "never_stream": True,
    })
    lib.save_loaded_asset(texture, only_if_is_dirty=False)

    plate = create_clean_material("M_Cairnwell_PR004_RobotPlate_v020", BRAND_ROOT)
    plate.set_editor_properties({"two_sided": True, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
    sample = expression(plate, unreal.MaterialExpressionTextureSample, -420, -80)
    sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
    mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    emissive_strength = expression(plate, unreal.MaterialExpressionConstant, -420, 80)
    emissive_strength.set_editor_property("r", 0.035)
    emissive = expression(plate, unreal.MaterialExpressionMultiply, -180, 20)
    mel.connect_material_expressions(sample, "RGB", emissive, "A")
    mel.connect_material_expressions(emissive_strength, "", emissive, "B")
    mel.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    rough = expression(plate, unreal.MaterialExpressionConstant, -180, 150)
    rough.set_editor_property("r", 0.48)
    metal = expression(plate, unreal.MaterialExpressionConstant, -180, 220)
    metal.set_editor_property("r", 0.04)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(plate)
    lib.save_loaded_asset(plate, only_if_is_dirty=False)

    carrier = create_clean_material("M_Cairnwell_RobotPlateCarrier_v020", BRAND_ROOT)
    carrier.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
    colour = expression(carrier, unreal.MaterialExpressionConstant3Vector, -260, -40)
    colour.set_editor_property("constant", unreal.LinearColor(0.018, 0.12, 0.085, 1.0))
    carrier_rough = expression(carrier, unreal.MaterialExpressionConstant, -260, 80)
    carrier_rough.set_editor_property("r", 0.46)
    carrier_metal = expression(carrier, unreal.MaterialExpressionConstant, -260, 150)
    carrier_metal.set_editor_property("r", 0.42)
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(carrier_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(carrier_metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(carrier)
    lib.save_loaded_asset(carrier, only_if_is_dirty=False)
    return texture, plate, carrier


def bounds_values(mesh):
    box = mesh.get_bounding_box()
    return {
        "min": [box.min.x, box.min.y, box.min.z],
        "max": [box.max.x, box.max.y, box.max.z],
    }


def collision_counts(mesh):
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is None:
        raise RuntimeError(f"No BodySetup after collision generation: {mesh.get_path_name()}")
    aggregate = body_setup.get_editor_property("agg_geom")
    return {
        "boxes": len(aggregate.get_editor_property("box_elems")),
        "spheres": len(aggregate.get_editor_property("sphere_elems")),
        "capsules": len(aggregate.get_editor_property("sphyl_elems")),
        "convex": len(aggregate.get_editor_property("convex_elems")),
    }


def duplicate_finish_mesh(module_id):
    record = IMPORT_MODULES[module_id]
    source_package = package_path(record["asset"])
    destination = f"{MESH_ROOT}/{asset_name(record['asset']).replace('_v002', '_v020')}"
    if lib.does_asset_exist(destination):
        raise RuntimeError(f"Refusing to overwrite preserved candidate mesh {destination}")
    if not lib.duplicate_asset(source_package, destination):
        raise RuntimeError(f"Could not duplicate {source_package} to {destination}")
    mesh = require_asset(destination, unreal.StaticMesh)
    before_bounds = bounds_values(mesh)
    dynamic = unreal.DynamicMesh()
    copy_from = unreal.GeometryScriptCopyMeshFromAssetOptions()
    copy_from.set_editor_properties({
        "apply_build_settings": True,
        "ignore_remove_degenerates": False,
        "request_tangents": True,
        "use_build_scale": True,
    })
    read_lod = unreal.GeometryScriptMeshReadLOD()
    unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh, dynamic, copy_from, read_lod)
    geometry_before = dynamic.get_mesh_info_string()
    repair = unreal.GeometryScriptDegenerateTriangleOptions()
    repair.set_editor_properties({
        "compact_on_completion": True,
        "min_edge_length": 0.0001,
        "min_triangle_area": 0.00000001,
    })
    unreal.GeometryScript_MeshRepair.repair_mesh_degenerate_geometry(dynamic, repair)
    unreal.GeometryScript_MeshRepair.compact_mesh(dynamic)
    geometry_after = dynamic.get_mesh_info_string()
    copy_to = unreal.GeometryScriptCopyMeshToAssetOptions()
    copy_to.set_editor_properties({
        "enable_recompute_normals": False,
        "enable_recompute_tangents": True,
        "enable_remove_degenerates": True,
        "clean_assigned_materials": False,
        "use_build_scale": True,
    })
    write_lod = unreal.GeometryScriptMeshWriteLOD()
    unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic, mesh, copy_to, write_lod, True)

    collision_options = unreal.GeometryScriptCollisionFromMeshOptions()
    collision_options.set_editor_properties({
        "method": unreal.GeometryScriptCollisionGenerationMethod.CONVEX_HULLS,
        "auto_detect_boxes": True,
        "auto_detect_capsules": True,
        "auto_detect_spheres": True,
        "convex_hull_target_face_count": 24,
        "convex_hull_geometric_tolerance": 0.25,
        "max_convex_hulls_per_mesh": 4,
        "max_shape_count": 8,
        "min_thickness": 0.5,
        "remove_fully_contained_shapes": True,
        "simplify_hulls": True,
        "emit_transaction": False,
    })
    set_options = unreal.GeometryScriptSetStaticMeshCollisionOptions()
    set_options.set_editor_property("mark_as_customized", True)
    unreal.GeometryScript_Collision.set_static_mesh_collision_from_mesh(dynamic, mesh, collision_options, set_options)
    body_setup = mesh.get_editor_property("body_setup")
    body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body_setup.modify()
    mesh.modify()
    lib.save_loaded_asset(mesh, only_if_is_dirty=False)
    counts = collision_counts(mesh)
    if sum(counts.values()) <= 0:
        raise RuntimeError(f"No simple collision generated for {module_id}: {destination}")
    after_bounds = bounds_values(mesh)
    return mesh, {
        "module_id": module_id,
        "source": source_package,
        "candidate": destination,
        "geometry_before": geometry_before,
        "geometry_after": geometry_after,
        "bounds_before_cm": before_bounds,
        "bounds_after_cm": after_bounds,
        "simple_collision": counts,
        "collision_trace_flag": str(body_setup.get_editor_property("collision_trace_flag")),
    }


def local_delta(child_id, parent_id):
    child = SOURCE_MODULES[child_id]
    parent = SOURCE_MODULES[parent_id]
    cx, cy, cz = child["assembly_location_cm"]
    px, py, pz = parent["assembly_location_cm"]
    yaw = math.radians(parent["assembly_rotation_deg"][2])
    dx, dy = cx - px, cy - py
    return (
        math.cos(yaw) * dx + math.sin(yaw) * dy,
        -math.sin(yaw) * dx + math.cos(yaw) * dy,
        cz - pz,
    )


def create_blueprint(path):
    if lib.does_asset_exist(path):
        raise RuntimeError(f"Refusing to overwrite preserved candidate Blueprint {path}")
    blueprint = bp_lib.create_blueprint_asset_with_parent(path, unreal.Actor)
    if blueprint is None:
        raise RuntimeError(f"Could not create Blueprint {path}")
    return blueprint


def root_handle(blueprint):
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    for handle in handles:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        if data_lib.is_default_scene_root(data):
            return handle
    if not handles:
        raise RuntimeError(f"Blueprint has no root handles: {blueprint.get_path_name()}")
    return handles[-1]


def add_component(blueprint, parent, component_class, name):
    params = unreal.AddNewSubobjectParams(
        parent_handle=parent,
        new_class=component_class,
        blueprint_context=blueprint,
        conform_transform_to_parent=False,
        skip_mark_blueprint_modified=False,
    )
    result = subsystem.add_new_subobject(params=params)
    handle = result[0]
    failure = str(result[1]) if len(result) > 1 else ""
    if not data_lib.is_handle_valid(handle):
        raise RuntimeError(f"Could not add {name}: {failure}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_lib.get_object_for_blueprint(data, blueprint)
    if component is None:
        component = data_lib.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component template {name}")
    return handle, component


def set_relative(component, location, rotation=(0.0, 0.0, 0.0)):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("relative_rotation", unreal.Rotator(*rotation))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)


def apply_cast_iron_overrides(component, module_id, surface_material):
    assignments = IMPORT_MODULES[module_id]["opaque_material_assignments"]
    if component.get_num_materials() != len(assignments):
        raise RuntimeError(
            f"Material slot mismatch for {module_id}: {component.get_num_materials()} != {len(assignments)}"
        )
    overrides = []
    for index, assignment in enumerate(assignments):
        if assignment["material_key"] != "CastIron":
            continue
        component.set_material(index, surface_material)
        overrides.append({
            "index": index,
            "source_slot": assignment["slot"],
            "semantic": assignment["material_key"],
            "material": surface_material.get_path_name(),
        })
    return overrides


def add_mesh_component(blueprint, parent, module_id, name, location, surface_material, meshes, rotation=(0, 0, 0)):
    handle, component = add_component(blueprint, parent, unreal.StaticMeshComponent, name)
    component.set_static_mesh(meshes[module_id])
    set_relative(component, location, rotation)
    overrides = apply_cast_iron_overrides(component, module_id, surface_material)
    return handle, component, overrides


def build_tool(definition, surface_material, meshes):
    tool_id, blueprint_name, body_id, children, location_overrides = definition
    path = f"{TOOL_ROOT}/{blueprint_name}"
    blueprint = create_blueprint(path)
    root = root_handle(blueprint)
    body_handle, _body, body_overrides = add_mesh_component(
        blueprint, root, body_id, "ToolBody", (0.0, 0.0, 0.0), surface_material, meshes
    )
    rows = [{
        "component": "ToolBody",
        "module_id": body_id,
        "parent": "DefaultSceneRoot",
        "cast_iron_overrides": body_overrides,
    }]
    for child_id, component_name in children:
        location = location_overrides.get(child_id, local_delta(child_id, body_id))
        _handle, _component, overrides = add_mesh_component(
            blueprint, body_handle, child_id, component_name, location, surface_material, meshes
        )
        rows.append({
            "component": component_name,
            "module_id": child_id,
            "parent": "ToolBody",
            "relative_location_cm": list(location),
            "cast_iron_overrides": overrides,
        })
    bp_lib.compile_blueprint(blueprint)
    if not lib.save_loaded_asset(blueprint, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save tool Blueprint {path}")
    return tool_id, blueprint, {"asset": path, "body": body_id, "components": rows}


def build_core(surface_material, meshes, tools, plate_material, carrier_material):
    path = ASSET_ROOT + "/BP_LB_Modular6AxisRobot_400kg_v020"
    blueprint = create_blueprint(path)
    root = root_handle(blueprint)
    handles = {}
    rows = []
    for module_id, component_name, parent_id in CORE_COMPONENTS:
        parent = handles[parent_id] if parent_id else root
        location = local_delta(module_id, parent_id) if parent_id else tuple(SOURCE_MODULES[module_id]["assembly_location_cm"])
        handle, _component, overrides = add_mesh_component(
            blueprint, parent, module_id, component_name, location, surface_material, meshes
        )
        handles[module_id] = handle
        rows.append({
            "component": component_name,
            "module_id": module_id,
            "parent": parent_id or "DefaultSceneRoot",
            "relative_location_cm": list(location),
            "cast_iron_overrides": overrides,
        })

    mount_handle, mount = add_component(blueprint, handles["changer_body"], unreal.SceneComponent, "ToolMount")
    set_relative(mount, (0.0, 0.0, 0.0))
    band_blueprint = tools["BandCutterCapture"]
    equipped_handle, equipped = add_component(blueprint, mount_handle, unreal.ChildActorComponent, "EquippedTool")
    equipped.set_editor_property("child_actor_class", bp_lib.generated_class(band_blueprint))
    set_relative(equipped, (0.0, 0.0, 0.0))
    rows.extend([
        {"component": "ToolMount", "module_id": None, "parent": "changer_body"},
        {
            "component": "EquippedTool",
            "module_id": "BandCutterCapture",
            "parent": "ToolMount",
            "replaceable_child_actor_class": True,
        },
    ])

    carrier_handle, carrier = add_component(
        blueprint, handles["j3"], unreal.StaticMeshComponent, "CairnwellPlateCarrier_v020"
    )
    carrier.set_static_mesh(require_asset("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh))
    set_relative(carrier, (52.0, -49.8, 8.0))
    carrier.set_editor_property("relative_scale3d", unreal.Vector(0.44, 0.006, 0.17))
    carrier.set_material(0, carrier_material)
    face_handle, face = add_component(
        blueprint, handles["j3"], unreal.StaticMeshComponent, "RobotAssetPlateFace_v020"
    )
    face.set_static_mesh(require_asset("/Engine/BasicShapes/Plane.Plane", unreal.StaticMesh))
    set_relative(face, (52.0, -50.45, 8.0), (90.0, 0.0, 0.0))
    face.set_editor_property("relative_scale3d", unreal.Vector(0.42, 0.1575, 1.0))
    face.set_material(0, plate_material)
    rows.extend([
        {
            "component": "CairnwellPlateCarrier_v020",
            "parent": "j3",
            "dimensions_cm": [44.0, 0.6, 17.0],
            "material": carrier_material.get_path_name(),
        },
        {
            "component": "RobotAssetPlateFace_v020",
            "parent": "j3",
            "dimensions_cm": [42.0, 15.75],
            "material": plate_material.get_path_name(),
        },
    ])

    variable_specs = [
        ("StationId", "string"),
        ("EquipmentId", "string"),
        ("ConditionAgeYears", "real"),
        ("ConditionSeed", "int"),
        ("CurrentToolId", "string"),
        ("J1Degrees", "real"),
        ("J2Degrees", "real"),
        ("J3Degrees", "real"),
        ("J4Degrees", "real"),
        ("J5Degrees", "real"),
        ("J6Degrees", "real"),
        ("Enabled", "bool"),
        ("ToolLocked", "bool"),
        ("FaultCode", "string"),
        ("OperatingHours", "real"),
        ("ServiceCycles", "int"),
    ]
    variables = []
    for variable_name, type_name in variable_specs:
        pin_type = bp_lib.get_basic_type_by_name(type_name)
        if not bp_lib.add_member_variable(blueprint, variable_name, pin_type):
            raise RuntimeError(f"Could not add reusable variable {variable_name}:{type_name}")
        bp_lib.set_blueprint_variable_instance_editable(blueprint, variable_name, True)
        variables.append({"name": variable_name, "type": type_name, "instance_editable": True})
    bp_lib.compile_blueprint(blueprint)
    if not lib.save_loaded_asset(blueprint, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save core Blueprint {path}")
    return blueprint, rows, variables


def place_candidate(core_blueprint):
    if not lib.does_asset_exist(BASE_MAP):
        raise RuntimeError(f"Missing accepted reusable source map {BASE_MAP}")
    if lib.does_asset_exist(DEST_MAP):
        raise RuntimeError(f"Refusing to overwrite preserved candidate map {DEST_MAP}")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.new_level_from_template(DEST_MAP, BASE_MAP):
        raise RuntimeError(f"Could not create {DEST_MAP} from {BASE_MAP}")
    source_robots = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == SOURCE_ROBOT_LABEL]
    if len(source_robots) != 1:
        raise RuntimeError(f"Expected one v016 source robot, found {len(source_robots)}")
    source_robot = source_robots[0]
    location = source_robot.get_actor_location()
    rotation = source_robot.get_actor_rotation()
    scale = source_robot.get_actor_scale3d()
    actors.destroy_actor(source_robot)
    robot = actors.spawn_actor_from_class(bp_lib.generated_class(core_blueprint), location, rotation)
    robot.set_actor_label(DEST_ROBOT_LABEL)
    robot.set_actor_scale3d(scale)
    robot.set_editor_property("tags", [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Equipment.Robot.Modular6Axis"),
        unreal.Name("LB.Station.PR004"),
        unreal.Name("LB.Tool.BandCutterCapture"),
        unreal.Name("LB.Material.SurfaceForgeSelective"),
        unreal.Name("LB.Brand.Cairnwell"),
    ])
    state = {
        "StationId": "PR-004",
        "EquipmentId": "PR004-RBT-01",
        "ConditionAgeYears": 7.0,
        "ConditionSeed": 4001,
        "CurrentToolId": "BandCutterCapture",
        "J1Degrees": 0.0,
        "J2Degrees": 0.0,
        "J3Degrees": 0.0,
        "J4Degrees": 0.0,
        "J5Degrees": 0.0,
        "J6Degrees": 0.0,
        "Enabled": False,
        "ToolLocked": True,
        "FaultCode": "RESTORATION_REQUIRED",
        "OperatingHours": 18420.0,
        "ServiceCycles": 318500,
    }
    for name, value in state.items():
        robot.set_editor_property(name, value)
    verified = {name: robot.get_editor_property(name) for name in state}
    if verified != state:
        raise RuntimeError(f"Reusable state mismatch: {verified}")
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save {DEST_MAP}")
    return robot, location, rotation, scale, verified


def main():
    surface_master, surface_instance = build_surface_material()
    plate_texture, plate_material, carrier_material = build_plate_materials()

    used_module_ids = [module_id for module_id, _name, _parent in CORE_COMPONENTS]
    for _tool_id, _bp_name, body_id, children, _overrides in TOOL_DEFINITIONS:
        used_module_ids.append(body_id)
        used_module_ids.extend(module_id for module_id, _name in children)
    if len(used_module_ids) != len(set(used_module_ids)):
        raise RuntimeError("Duplicate module ids in v020 reusable contract")
    meshes = {}
    mesh_rows = []
    for index, module_id in enumerate(used_module_ids, start=1):
        unreal.log(f"LINE_BOSS_PR004_V020_GEOMETRY {index}/{len(used_module_ids)} {module_id}")
        mesh, row = duplicate_finish_mesh(module_id)
        meshes[module_id] = mesh
        mesh_rows.append(row)

    tool_blueprints = {}
    tool_rows = []
    for definition in TOOL_DEFINITIONS:
        tool_id, blueprint, row = build_tool(definition, surface_instance, meshes)
        tool_blueprints[tool_id] = blueprint
        tool_rows.append(row)
    core, core_rows, variables = build_core(
        surface_instance, meshes, tool_blueprints, plate_material, carrier_material
    )
    robot, location, rotation, scale, state = place_candidate(core)

    cast_iron_override_count = sum(
        len(row.get("cast_iron_overrides", [])) for row in core_rows
    ) + sum(
        len(component.get("cast_iron_overrides", []))
        for tool in tool_rows for component in tool["components"]
    )
    payload = {
        "$schema": "line-boss/audit/press-shop-pr004-surfaceforge-robot-candidate-v020/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ISOLATED_SURFACEFORGE_GEOMETRYSCRIPT_REUSABLE_ROBOT_CANDIDATE__NOT_PROMOTED",
        "accepted_integration_baseline": ACCEPTED_INTEGRATION_BASELINE,
        "reusable_composition_source": BASE_MAP,
        "candidate_map": DEST_MAP,
        "candidate_blueprint": core.get_path_name(),
        "robot_actor": robot.get_actor_label(),
        "robot_transform": {
            "location_cm": [location.x, location.y, location.z],
            "rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
            "scale": [scale.x, scale.y, scale.z],
        },
        "instance_state": state,
        "surface_forge": {
            "selection_policy": "Three original Metal_Paint_Chips PBR textures only; no pack master/dependency closure copied.",
            "source_textures": [SURFACE_BASE, SURFACE_NORMAL, SURFACE_ORD],
            "master": surface_master.get_path_name(),
            "instance": surface_instance.get_path_name(),
            "semantic_scope": "CastIron slots only",
            "cast_iron_override_count": cast_iron_override_count,
            "paint_colour": "Cairnwell green",
            "wear_policy": "restrained via PaintCoverageBias=0.72; source orange is used only to derive a mask",
        },
        "cairnwell_branding": {
            "texture": plate_texture.get_path_name(),
            "material": plate_material.get_path_name(),
            "carrier_material": carrier_material.get_path_name(),
            "equipment_id": "PR004-RBT-01",
            "internal_project_use_gate": "CLEARED_BY_USER_CONFIRMATION",
            "formal_trademark_clearance": False,
        },
        "geometry_script": {
            "engine": str(unreal.SystemLibrary.get_engine_version()),
            "mesh_count": len(mesh_rows),
            "operations": ["copy", "repair_degenerate_geometry", "compact_mesh", "copy_to_static_mesh"],
            "source_meshes_modified": False,
            "candidate_meshes": mesh_rows,
        },
        "collision": {
            "method": "GeometryScriptCollisionGenerationMethod.CONVEX_HULLS",
            "max_convex_hulls_per_mesh": 4,
            "trace_flag": "CTF_USE_DEFAULT",
            "all_candidate_meshes_have_simple_collision": all(
                sum(row["simple_collision"].values()) > 0 for row in mesh_rows
            ),
            "swept_articulation_runtime_gate": "OPEN",
        },
        "robot_core_components": core_rows,
        "tool_blueprints": tool_rows,
        "instance_variables": variables,
        "source_assets_preserved": True,
        "rejected_candidate_assets_reused": False,
        "technical_gate": "BUILD_COMPLETE__SEPARATE_AUDIT_REQUIRED",
        "runtime_gate": "OPEN",
        "save_load_gate": "OPEN",
        "fresh_fixed_camera_visual_gate": "OPEN",
        "promotion_authorized": False,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(
        f"LINE_BOSS_PR004_SURFACEFORGE_ROBOT_V020_PASS meshes={len(mesh_rows)} "
        f"castiron={cast_iron_override_count} audit={AUDIT_PATH}"
    )
    unreal.SystemLibrary.quit_editor()


main()
