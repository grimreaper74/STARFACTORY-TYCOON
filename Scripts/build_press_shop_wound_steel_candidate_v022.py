"""Create and apply a contained procedural wound-steel material in v022."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_WoundSteelFrontEndCandidate_v022"
MATERIAL_ROOT = "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v022"
MATERIAL_PATH = MATERIAL_ROOT + "/M_LB_BareCoil_WoundSteel_v022"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_wound_steel_candidate_v022.json"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(MAP):
    raise RuntimeError(f"Prepared map missing: {MAP}")
if lib.does_asset_exist(MATERIAL_PATH):
    raise RuntimeError(f"Refusing to overwrite preserved material {MATERIAL_PATH}")

material = tools.create_asset(
    "M_LB_BareCoil_WoundSteel_v022",
    MATERIAL_ROOT,
    unreal.Material,
    unreal.MaterialFactoryNew(),
)
if material is None:
    raise RuntimeError("Could not create v022 wound-steel material")
material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})

def expr(cls, x, y):
    return mel.create_material_expression(material, cls, x, y)

uv = expr(unreal.MaterialExpressionTextureCoordinate, -1050, -160)
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
variation_amount.set_editor_property("r", 0.42)
mel.connect_material_expressions(absolute, "", variation, "A")
mel.connect_material_expressions(variation_amount, "", variation, "B")

dark = expr(unreal.MaterialExpressionConstant3Vector, -60, -320)
dark.set_editor_property("constant", unreal.LinearColor(0.16, 0.175, 0.19, 1.0))
light = expr(unreal.MaterialExpressionConstant3Vector, -60, -245)
light.set_editor_property("constant", unreal.LinearColor(0.34, 0.36, 0.39, 1.0))
colour = expr(unreal.MaterialExpressionLinearInterpolate, 180, -250)
mel.connect_material_expressions(dark, "", colour, "A")
mel.connect_material_expressions(light, "", colour, "B")
mel.connect_material_expressions(variation, "", colour, "Alpha")
mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)

roughness = expr(unreal.MaterialExpressionConstant, 180, -80)
roughness.set_editor_property("r", 0.34)
metallic = expr(unreal.MaterialExpressionConstant, 180, 0)
metallic.set_editor_property("r", 0.92)
specular = expr(unreal.MaterialExpressionConstant, 180, 80)
specular.set_editor_property("r", 0.62)
mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
mel.recompile_material(material)
lib.save_loaded_asset(material, only_if_is_dirty=False)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
changed = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if "BareMasterCoil_v021" not in label and label != "LB_INT_PR004_V009_packaging_v004_PR004_PACK_BARE_COIL_v004":
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        raise RuntimeError(f"Bare coil lacks StaticMeshComponent: {label}")
    component.set_material(0, material)
    actor.tags = list(actor.tags) + [
        unreal.Name("LB.Asset.Candidate.v022"),
        unreal.Name("LB.Material.WoundSteel"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    changed.append(label)

if len(changed) != 15:
    raise RuntimeError(f"Expected 15 bare coils including PR-004, changed {len(changed)}")
if not levels.save_current_level():
    raise RuntimeError("Could not save v022 map")

payload = {
    "$schema": "line-boss/audit/press-shop-wound-steel-candidate-v022/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_WOUND_STEEL_CANDIDATE__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_BareCoilFrontEndCandidate_v021",
    "candidate_map": MAP,
    "material": material.get_path_name(),
    "material_contract": {
        "dark_linear_rgb": [0.16, 0.175, 0.19],
        "light_linear_rgb": [0.34, 0.36, 0.39],
        "winding_frequency": 185.0,
        "variation": 0.42,
        "metallic": 0.92,
        "roughness": 0.34,
        "specular": 0.62
    },
    "changed_actor_count": len(changed),
    "changed_actors": changed,
    "accepted_v006_preserved": True,
    "v021_preserved": True,
    "surface_forge_used": False,
    "surface_forge_reason": "Installed pack contains paint-chip textures only; unsuitable for bare wound steel.",
    "fresh_fixed_camera_visual_gate": "OPEN",
    "promotion_authorized": False
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_WOUND_STEEL_V022_BUILD_PASS changed={len(changed)} output={OUTPUT}")
unreal.SystemLibrary.quit_editor()
