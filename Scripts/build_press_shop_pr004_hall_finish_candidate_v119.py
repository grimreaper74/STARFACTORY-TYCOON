"""Build isolated v119 hall finish and restrained wall lighting from v118."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v119"
DEST = "/Game/LineBoss/Candidates/PressShop/PR004HallFinish_v119"
OUT = ROOT / "Saved/Audits/press_shop_pr004_hall_finish_build_v119.json"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create isolated v119 from {BASE}")


def constant_material(name, colour, roughness, metallic=0.0):
    material = tools.create_asset(name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(name)
    colour_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -260, -40)
    colour_node.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 80)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 150)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(colour_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "lower_concrete": constant_material("M_CA_MW_HallLowerConcrete_v119", (0.18, 0.19, 0.20), 0.86),
    "upper_panel": constant_material("M_CA_MW_HallUpperServicePanel_v119", (0.075, 0.090, 0.105), 0.80),
    "painted_steel": constant_material("M_CA_MW_HallPaintedSteel_v119", (0.095, 0.115, 0.135), 0.54, 0.42),
}

changed = []
hidden_superseded = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    role = None
    if label == "LB_INT_FRONT_NorthWallLowerLiner":
        role = "lower_concrete"
    elif label in ("LB_INT_FRONT_NorthWallUpperLiner", "LB_INT_FRONT_WestWallLiner"):
        role = "upper_panel"
    elif label.startswith("LB_INT_FRONT_NorthWallColumn_") or label.startswith("LB_INT_FRONT_NorthWallBeam_"):
        role = "painted_steel"
    elif label.startswith("LB_PR004_V028_SouthWallLiner_"):
        # These five earlier panels overlap the integrated north-wall liner and
        # create the striped/z-fighting read. Preserve them but disable display.
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.set_actor_hidden_in_game(True)
        prior_tags = [str(value) for value in actor.tags]
        actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
            "LB.Asset.Candidate.v119", "LB.Environment.Wall.SupersededVisualHidden"
        ])]
        hidden_superseded.append(label)
        continue
    if role is None:
        continue
    component = actor.static_mesh_component
    before = []
    for index in range(max(1, component.get_num_materials())):
        old = component.get_material(index)
        before.append(old.get_path_name() if old else None)
        component.set_material(index, materials[role])
    prior_tags = [str(value) for value in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
        "LB.Asset.Candidate.v119", f"LB.Environment.HallFinish.{role}"
    ])]
    changed.append({"actor": label, "role": role, "before": before,
                    "after": materials[role].get_path_name()})

# Broad, low-intensity wall wash reveals installed structure without bleaching
# the package, floor, HMI, or crane task area.
wall_wash = []
for index, x in enumerate((-10000.0, -8200.0, -6400.0, -4600.0), start=1):
    light = actors_api.spawn_actor_from_class(
        unreal.SpotLight, unreal.Vector(x, -4700.0, 1450.0), unreal.Rotator())
    light.set_actor_label(f"LB_PR004_V119_HallWallWash_{index:02d}")
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        light.get_actor_location(), unreal.Vector(x, -5925.0, 1050.0)), False)
    light.spot_light_component.set_editor_properties({
        "intensity": 360.0,
        "attenuation_radius": 1850.0,
        "inner_cone_angle": 38.0,
        "outer_cone_angle": 72.0,
        "source_radius": 85.0,
        "soft_source_radius": 170.0,
        "cast_shadows": False,
        "light_color": unreal.Color(210, 222, 228, 255),
    })
    light.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v119", "LB.Asset.CandidateNotPromoted",
        "LB.Lighting.HallWallWash", "LB.Environment.HallFinish.v119")]
    wall_wash.append(light.get_actor_label())

failures = []
if len(hidden_superseded) != 5:
    failures.append(f"expected five superseded v028 wall panels, found {len(hidden_superseded)}")
if len(changed) != 31:
    failures.append(f"expected 31 current liner/column/beam bindings, changed {len(changed)}")
if len(wall_wash) != 4:
    failures.append(f"expected four wall-wash lights, found {len(wall_wash)}")
if not levels.save_current_level():
    failures.append("could not save isolated v119")
lib.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-shop-pr004-hall-finish-build-v119/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_V119_NONREPEATING_HALL_FINISH_AND_WALL_WASH_BUILT__VISUAL_AND_EXACT_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V119_HALL_FINISH_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "changed_surface_count": len(changed),
    "hidden_superseded_visuals": sorted(hidden_superseded),
    "wall_wash_lights": wall_wash,
    "geometry_deleted": False,
    "collision_or_navigation_changed": False,
    "machinery_or_gameplay_authority_changed": False,
    "v118_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "changed": len(changed), "hidden": len(hidden_superseded), "lights": len(wall_wash), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
