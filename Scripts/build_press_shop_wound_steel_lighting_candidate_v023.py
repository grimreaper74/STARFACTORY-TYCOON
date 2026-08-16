"""Build a contained wound-steel plus reflection/lighting candidate in v023."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_WoundSteelLightingCandidate_v023"
MATERIAL_ROOT = "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v023"
MATERIAL_PATH = MATERIAL_ROOT + "/M_LB_BareCoil_WoundSteel_v023"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_wound_steel_lighting_candidate_v023.json"
COIL_LABEL_PR004 = "LB_INT_PR004_V009_packaging_v004_PR004_PACK_BARE_COIL_v004"
LOCAL_FILL_INTENSITIES = {
    "LB_INT_FRONT_FactoryFill_11": 1450.0,
    "LB_INT_FRONT_FactoryFill_12": 1100.0,
    "LB_INT_FRONT_FactoryFill_14": 1250.0,
}

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(MAP):
    raise RuntimeError(f"Prepared map missing: {MAP}")
material = lib.load_asset(MATERIAL_PATH) if lib.does_asset_exist(MATERIAL_PATH) else tools.create_asset(
    "M_LB_BareCoil_WoundSteel_v023",
    MATERIAL_ROOT,
    unreal.Material,
    unreal.MaterialFactoryNew(),
)
if material is None:
    raise RuntimeError("Could not create or load v023 wound-steel material")
material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})


def expr(cls, x, y):
    return mel.create_material_expression(material, cls, x, y)


if not mel.get_material_expressions(material):
    uv = expr(unreal.MaterialExpressionTextureCoordinate, -1050, -160)
else:
    uv = None
if uv is not None:
    mask_u = expr(unreal.MaterialExpressionComponentMask, -850, -160)
    mask_u.set_editor_properties({"r": True, "g": False, "b": False, "a": False})
    mel.connect_material_expressions(uv, "", mask_u, "Input")
    frequency = expr(unreal.MaterialExpressionConstant, -850, -40)
    frequency.set_editor_property("r", 185.0)
    scaled = expr(unreal.MaterialExpressionMultiply, -650, -140)
    mel.connect_material_expressions(mask_u, "", scaled, "A")
    mel.connect_material_expressions(frequency, "", scaled, "B")
    wave = expr(unreal.MaterialExpressionSine, -450, -140)
    mel.connect_material_expressions(scaled, "", wave, "Input")
    absolute = expr(unreal.MaterialExpressionAbs, -260, -140)
    mel.connect_material_expressions(wave, "", absolute, "Input")
    variation = expr(unreal.MaterialExpressionMultiply, -60, -140)
    variation_amount = expr(unreal.MaterialExpressionConstant, -260, -20)
    variation_amount.set_editor_property("r", 0.34)
    mel.connect_material_expressions(absolute, "", variation, "A")
    mel.connect_material_expressions(variation_amount, "", variation, "B")

    dark = expr(unreal.MaterialExpressionConstant3Vector, -60, -320)
    dark.set_editor_property("constant", unreal.LinearColor(0.24, 0.26, 0.29, 1.0))
    light = expr(unreal.MaterialExpressionConstant3Vector, -60, -245)
    light.set_editor_property("constant", unreal.LinearColor(0.48, 0.50, 0.54, 1.0))
    colour = expr(unreal.MaterialExpressionLinearInterpolate, 180, -250)
    mel.connect_material_expressions(dark, "", colour, "A")
    mel.connect_material_expressions(light, "", colour, "B")
    mel.connect_material_expressions(variation, "", colour, "Alpha")
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)

    roughness = expr(unreal.MaterialExpressionConstant, 180, -80)
    roughness.set_editor_property("r", 0.38)
    metallic = expr(unreal.MaterialExpressionConstant, 180, 0)
    metallic.set_editor_property("r", 0.80)
    specular = expr(unreal.MaterialExpressionConstant, 180, 80)
    specular.set_editor_property("r", 0.58)
    mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

changed_coils = []
light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if "BareMasterCoil_v021" in label or label == COIL_LABEL_PR004:
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if component is None:
            raise RuntimeError(f"Bare coil lacks StaticMeshComponent: {label}")
        component.set_material(0, material)
        actor.tags = list(actor.tags) + [
            unreal.Name("LB.Asset.Candidate.v023"),
            unreal.Name("LB.Material.WoundSteel"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        changed_coils.append(label)
    if label in LOCAL_FILL_INTENSITIES:
        component = actor.get_editor_property("point_light_component")
        before = float(component.get_editor_property("intensity"))
        after = LOCAL_FILL_INTENSITIES[label]
        component.set_editor_property("intensity", after)
        light_changes.append({"actor": label, "before": before, "after": after})

if len(changed_coils) != 15:
    raise RuntimeError(f"Expected 15 bare coils including PR-004, changed {len(changed_coils)}")
if len(light_changes) != len(LOCAL_FILL_INTENSITIES):
    raise RuntimeError(f"Expected {len(LOCAL_FILL_INTENSITIES)} local fills, changed {len(light_changes)}")

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(-5050.0, -2000.0, 900.0), unreal.Rotator())
if sky is None:
    raise RuntimeError("Could not spawn v023 SkyLight")
sky.set_actor_label("LB_PRESS_V023_FrontEndSkyLight")
sky.tags = [unreal.Name("LB.Asset.Candidate.v023"), unreal.Name("LB.Lighting.FrontEndMetal")]
sky_component = sky.get_editor_property("light_component")
sky_component.set_editor_properties({
    "intensity": 0.55,
    "real_time_capture": True,
    "source_type": unreal.SkyLightSourceType.SLS_CAPTURED_SCENE,
    "lower_hemisphere_is_black": False,
    "lower_hemisphere_color": unreal.LinearColor(0.055, 0.065, 0.08, 1.0),
    "affect_global_illumination": True,
    "affect_reflection": True,
})

reflection_specs = [
    ("LB_PRESS_V023_PR003_Reflection", unreal.Vector(-6450.0, -2000.0, 300.0), 1750.0),
    ("LB_PRESS_V023_PR004_Reflection", unreal.Vector(-5050.0, -2000.0, 300.0), 1600.0),
]
reflections = []
for label, location, radius in reflection_specs:
    capture = actors.spawn_actor_from_class(unreal.SphereReflectionCapture, location, unreal.Rotator())
    if capture is None:
        raise RuntimeError(f"Could not spawn reflection capture {label}")
    capture.set_actor_label(label)
    capture.tags = [unreal.Name("LB.Asset.Candidate.v023"), unreal.Name("LB.Reflection.FrontEndMetal")]
    component = capture.get_editor_property("capture_component")
    component.set_editor_properties({
        "influence_radius": radius,
        "brightness": 1.05,
        "runtime_capture": True,
        "reflection_source_type": unreal.ReflectionSourceType.CAPTURED_SCENE,
        "runtime_skylight_scale": unreal.LinearColor(0.16, 0.18, 0.22, 1.0),
    })
    reflections.append({"actor": label, "location_cm": [location.x, location.y, location.z], "radius_cm": radius})

if not levels.save_current_level():
    raise RuntimeError("Could not save v023 map")

payload = {
    "$schema": "line-boss/audit/press-shop-wound-steel-lighting-candidate-v023/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_WOUND_STEEL_LIGHTING_CANDIDATE__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_WoundSteelFrontEndCandidate_v022",
    "candidate_map": MAP,
    "material": material.get_path_name(),
    "material_contract": {
        "dark_linear_rgb": [0.24, 0.26, 0.29],
        "light_linear_rgb": [0.48, 0.50, 0.54],
        "winding_frequency": 185.0,
        "variation": 0.34,
        "metallic": 0.80,
        "roughness": 0.38,
        "specular": 0.58,
    },
    "changed_coil_count": len(changed_coils),
    "changed_coils": changed_coils,
    "local_fill_changes": sorted(light_changes, key=lambda item: item["actor"]),
    "sky_light": {"actor": sky.get_actor_label(), "intensity": 0.55, "real_time_capture": True},
    "reflection_captures": reflections,
    "accepted_v006_preserved": True,
    "v021_preserved": True,
    "v022_preserved": True,
    "equipment_coordinates_modified": False,
    "fresh_fixed_camera_visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_WOUND_STEEL_LIGHTING_V023_BUILD_PASS coils={len(changed_coils)} lights={len(light_changes)}")
unreal.SystemLibrary.quit_editor()
