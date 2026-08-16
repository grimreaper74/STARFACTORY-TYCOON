"""Build the release-facing, world-scale Line Boss factory floor material.

This material deliberately uses absolute world position instead of the 0..1 UVs
of the 220 m clean-shell cube.  The earlier front-end concrete master repeated
a pillar texture at hall scale and produced the rejected plank effect.

The base colour combines two cheap world-space noise bands.  A procedural
six-metre saw-cut grid is embedded in the shader below the separately generated
route/safety paint, so it never becomes collision or route authority.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Materials/Environment"
MASTER_NAME = "M_LB_SealedFactoryConcrete_World_v001"
INSTANCE_NAME = "MI_LB_SealedFactoryConcrete_Neutral_v001"
AUDIT = ROOT / "Saved/Audits/VisualTuning/factory_environment_materials_v001.json"


def expression(material, klass, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression(material, klass, x, y)


def connect(source, output_name, target, input_name):
    # UE 5.8's Python wrapper returns None for this mutating call even on a
    # successful connection, so the compiled material/validator is the gate.
    unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output_name, target, input_name
    )


def build_master():
    library = unreal.EditorAssetLibrary
    path = f"{DEST}/{MASTER_NAME}"
    material = library.load_asset(path) if library.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            MASTER_NAME, DEST, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Unexpected material asset at {path}")

    if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    material.set_editor_properties({"two_sided": False})

    world_position = expression(material, unreal.MaterialExpressionWorldPosition, -1500, 0)

    macro_noise = expression(material, unreal.MaterialExpressionNoise, -1220, -220)
    macro_noise.set_editor_properties({
        "scale": 0.0018,
        "quality": 1,
        "noise_function": unreal.NoiseFunction.NOISEFUNCTION_VALUE_ALU,
        "turbulence": True,
        "levels": 2,
        "output_min": 0.0,
        "output_max": 1.0,
        "level_scale": 2.0,
        "tiling": False,
    })
    connect(world_position, "", macro_noise, "Position")

    detail_noise = expression(material, unreal.MaterialExpressionNoise, -1220, 10)
    detail_noise.set_editor_properties({
        "scale": 0.012,
        "quality": 1,
        "noise_function": unreal.NoiseFunction.NOISEFUNCTION_VALUE_ALU,
        "turbulence": True,
        "levels": 1,
        "output_min": 0.0,
        "output_max": 1.0,
        "level_scale": 2.0,
        "tiling": False,
    })
    connect(world_position, "", detail_noise, "Position")

    macro_strength = expression(material, unreal.MaterialExpressionScalarParameter, -950, -310)
    macro_strength.set_editor_properties({
        "parameter_name": "MacroVariationStrength",
        "default_value": 0.055,
        "slider_min": 0.0,
        "slider_max": 0.15,
    })
    macro_scaled = expression(material, unreal.MaterialExpressionMultiply, -740, -220)
    connect(macro_noise, "", macro_scaled, "A")
    connect(macro_strength, "", macro_scaled, "B")

    detail_strength = expression(material, unreal.MaterialExpressionScalarParameter, -950, 100)
    detail_strength.set_editor_properties({
        "parameter_name": "FineVariationStrength",
        "default_value": 0.020,
        "slider_min": 0.0,
        "slider_max": 0.08,
    })
    detail_scaled = expression(material, unreal.MaterialExpressionMultiply, -740, 10)
    connect(detail_noise, "", detail_scaled, "A")
    connect(detail_strength, "", detail_scaled, "B")

    variation = expression(material, unreal.MaterialExpressionAdd, -500, -100)
    connect(macro_scaled, "", variation, "A")
    connect(detail_scaled, "", variation, "B")

    base_tint = expression(material, unreal.MaterialExpressionVectorParameter, -500, -320)
    base_tint.set_editor_properties({
        "parameter_name": "ConcreteTint",
        "default_value": unreal.LinearColor(0.285, 0.305, 0.315, 1.0),
    })
    brightened_base = expression(material, unreal.MaterialExpressionAdd, -260, -220)
    connect(base_tint, "", brightened_base, "A")
    connect(variation, "", brightened_base, "B")

    # Build a 6 m saw-cut mask in absolute XY world space. The mask is only a
    # colour variation in the base slab; the route paint remains separate.
    xy = expression(material, unreal.MaterialExpressionComponentMask, -1220, 340)
    xy.set_editor_properties({"r": True, "g": True, "b": False, "a": False})
    connect(world_position, "", xy, "Input")

    grid_scale = expression(material, unreal.MaterialExpressionScalarParameter, -950, 350)
    grid_scale.set_editor_properties({
        "parameter_name": "SlabSizeCm",
        "default_value": 600.0,
        "slider_min": 300.0,
        "slider_max": 1200.0,
    })
    scaled_xy = expression(material, unreal.MaterialExpressionDivide, -720, 340)
    connect(xy, "", scaled_xy, "A")
    connect(grid_scale, "", scaled_xy, "B")

    fractional_xy = expression(material, unreal.MaterialExpressionFrac, -500, 340)
    connect(scaled_xy, "", fractional_xy, "Input")
    centred_xy = expression(material, unreal.MaterialExpressionSubtract, -290, 340)
    centred_xy.set_editor_property("const_b", 0.5)
    connect(fractional_xy, "", centred_xy, "A")
    abs_xy = expression(material, unreal.MaterialExpressionAbs, -80, 340)
    connect(centred_xy, "", abs_xy, "Input")
    edge_distance = expression(material, unreal.MaterialExpressionComponentMask, 130, 340)
    edge_distance.set_editor_properties({"r": True, "g": True, "b": False, "a": False})
    connect(abs_xy, "", edge_distance, "Input")

    min_axis = expression(material, unreal.MaterialExpressionMin, 340, 340)
    connect(edge_distance, "R", min_axis, "A")
    connect(edge_distance, "G", min_axis, "B")
    half_minus_edge = expression(material, unreal.MaterialExpressionSubtract, 550, 340)
    half_minus_edge.set_editor_property("const_a", 0.5)
    connect(min_axis, "", half_minus_edge, "B")

    joint_width = expression(material, unreal.MaterialExpressionScalarParameter, 340, 510)
    joint_width.set_editor_properties({
        "parameter_name": "JointHalfWidthRatio",
        "default_value": 0.0025,
        "slider_min": 0.001,
        "slider_max": 0.01,
    })
    joint_softness = expression(material, unreal.MaterialExpressionScalarParameter, 550, 510)
    joint_softness.set_editor_properties({
        "parameter_name": "JointSoftnessRatio",
        "default_value": 0.0030,
        "slider_min": 0.001,
        "slider_max": 0.015,
    })
    joint_outer = expression(material, unreal.MaterialExpressionAdd, 760, 510)
    connect(joint_width, "", joint_outer, "A")
    connect(joint_softness, "", joint_outer, "B")
    joint_mask = expression(material, unreal.MaterialExpressionSmoothStep, 790, 340)
    connect(joint_width, "", joint_mask, "Min")
    connect(joint_outer, "", joint_mask, "Max")
    connect(half_minus_edge, "", joint_mask, "Value")
    joint_tint = expression(material, unreal.MaterialExpressionVectorParameter, 790, 160)
    joint_tint.set_editor_properties({
        "parameter_name": "JointTint",
        "default_value": unreal.LinearColor(0.095, 0.105, 0.11, 1.0),
    })
    final_colour = expression(material, unreal.MaterialExpressionLinearInterpolate, 1220, -100)
    # SmoothStep is 0 on a saw-cut and 1 across the slab field.  Put the
    # joint colour on A and the concrete on B so the mask can drive the Lerp
    # directly.  This avoids UE 5.8's fragile Python pin name for OneMinus,
    # which previously left its input disconnected in the runtime shader.
    connect(joint_tint, "", final_colour, "A")
    connect(brightened_base, "", final_colour, "B")
    connect(joint_mask, "", final_colour, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(
        final_colour, "", unreal.MaterialProperty.MP_BASE_COLOR
    )

    roughness = expression(material, unreal.MaterialExpressionScalarParameter, 1000, 60)
    roughness.set_editor_properties({
        "parameter_name": "Roughness",
        "default_value": 0.82,
        "slider_min": 0.65,
        "slider_max": 0.95,
    })
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    metallic = expression(material, unreal.MaterialExpressionConstant, 1000, 120)
    metallic.set_editor_property("r", 0.0)
    unreal.MaterialEditingLibrary.connect_material_property(
        metallic, "", unreal.MaterialProperty.MP_METALLIC
    )

    unreal.MaterialEditingLibrary.recompile_material(material)
    if not library.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {path}")
    return material


def build_instance(parent):
    library = unreal.EditorAssetLibrary
    path = f"{DEST}/{INSTANCE_NAME}"
    instance = library.load_asset(path) if library.does_asset_exist(path) else None
    if instance is None:
        instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            INSTANCE_NAME,
            DEST,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        raise RuntimeError(f"Unexpected material instance asset at {path}")

    instance.set_editor_property("parent", parent)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance, "ConcreteTint", unreal.LinearColor(0.285, 0.305, 0.315, 1.0)
    )
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance, "JointTint", unreal.LinearColor(0.095, 0.105, 0.11, 1.0)
    )
    for name, value in {
        "MacroVariationStrength": 0.055,
        "FineVariationStrength": 0.020,
        "SlabSizeCm": 600.0,
        "JointHalfWidthRatio": 0.0025,
        "JointSoftnessRatio": 0.0030,
        "Roughness": 0.82,
    }.items():
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            instance, name, value
        )
    if not library.save_loaded_asset(instance, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {path}")
    return instance


parent = build_master()
instance = build_instance(parent)

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(
    json.dumps(
        {
            "status": "PASS__WORLD_SCALE_FACTORY_FLOOR_MATERIAL_BUILT",
            "master": parent.get_path_name(),
            "instance": instance.get_path_name(),
            "projection": "absolute_world_position_procedural",
            "slab_size_cm": 600.0,
            "route_authority_changed": False,
            "collision_or_navigation_changed": False,
            "visual_gate_required": True,
        },
        indent=2,
    ),
    encoding="utf-8",
)
unreal.log(
    f"LINE_BOSS_FACTORY_ENVIRONMENT_MATERIAL_PASS master={parent.get_path_name()} "
    f"instance={instance.get_path_name()} audit={AUDIT}"
)
