"""Build an isolated v181 balanced-hall visual candidate from retained v180.

This preserves v180 coil readability and all runtime authority.  It replaces
the black shell read in the PR001-PR005 front-end envelope with restrained
light-grey industrial liner/roof materials and broad low-energy wall wash.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004BalancedHallCandidate_v181"
DEST = "/Game/LineBoss/Candidates/PressShop/PR003PR004BalancedHall_v181"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_balanced_hall_build_v181.json"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180.umap"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def constant_material(name, colour, roughness, metallic=0.0):
    material = tools.create_asset(name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {name}")
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


base_hash_before = sha256(BASE_PACKAGE)
if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create isolated v181 from {BASE}")

materials = {
    "lower_concrete": constant_material(
        "M_CA_MW_HallLowerConcrete_v181", (0.24, 0.25, 0.26), 0.88),
    "upper_panel": constant_material(
        "M_CA_MW_HallUpperServicePanel_v181", (0.29, 0.32, 0.34), 0.78),
    "painted_steel": constant_material(
        "M_CA_MW_HallPaintedSteel_v181", (0.055, 0.085, 0.12), 0.56, 0.36),
}

common_tags = [
    "LB.Asset.Candidate.v181", "LB.Asset.CandidateNotPromoted",
    "LB.Environment.BalancedHall.v181", "LB.VisualCorrection.HallReadability",
]
changed = []
hidden_superseded = []
roof_count = 0
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
    elif label.startswith("LB_PR004_V028_RoofLiner_"):
        role = "upper_panel"
        roof_count += 1
    elif label.startswith("LB_PR004_V028_SouthWallLiner_"):
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.set_actor_hidden_in_game(True)
        actor.tags = [unreal.Name(value) for value in dict.fromkeys(
            [str(value) for value in actor.tags] + common_tags +
            ["LB.Environment.Wall.SupersededVisualHidden"])]
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
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in actor.tags] + common_tags +
        [f"LB.Environment.HallFinish.{role}"])]
    changed.append({
        "actor": label, "role": role, "before": before,
        "after": materials[role].get_path_name(),
    })

wall_wash = []
for index, x in enumerate((-10000.0, -8000.0, -6000.0, -4000.0), start=1):
    location = unreal.Vector(x, -5000.0, 1050.0)
    target = unreal.Vector(x, -5930.0, 1080.0)
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    light = actors_api.spawn_actor_from_class(unreal.RectLight, location, rotation)
    light.set_actor_label(f"LB_ENV_V181_NorthWallBroadWash_{index:02d}")
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_properties({
        "intensity": 22.0,
        "source_width": 1750.0,
        "source_height": 1050.0,
        "attenuation_radius": 1450.0,
        "cast_shadows": False,
        "light_color": unreal.Color(211, 222, 226, 255),
    })
    light.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Light.WallWash"]]
    wall_wash.append(light.get_actor_label())


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name(value) for value in common_tags + [
        "LB.Camera.Validation", "LB.Camera.Fixed.BalancedHall.v181"]]
    return camera


cameras = [
    add_camera("LB_ENV_V181_CAM_FrontEndFlow", (-10600.0, 900.0, 980.0), (-7200.0, -2100.0, 520.0), 59.0),
    add_camera("LB_ENV_V181_CAM_PR003PR004Management", (-10300.0, 1450.0, 720.0), (-5900.0, -2850.0, 470.0), 62.0),
    add_camera("LB_ENV_V181_CAM_NorthWallCell", (-9600.0, 250.0, 660.0), (-6500.0, -5100.0, 850.0), 57.0),
]

failures = []
if len(changed) != 51:
    failures.append(f"expected 31 wall/structure plus 20 roof bindings, changed {len(changed)}")
if roof_count != 20:
    failures.append(f"expected 20 roof liners, found {roof_count}")
if len(hidden_superseded) != 5:
    failures.append(f"expected five overlapping v028 wall panels, found {len(hidden_superseded)}")
if len(wall_wash) != 4 or len(cameras) != 3:
    failures.append("unexpected wall-wash or fixed-camera count")
if not levels.save_current_level():
    failures.append("could not save isolated v181")
lib.save_directory(DEST, only_if_is_dirty=False, recursive=True)
base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("protected v180 package changed")

report = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-balanced-hall-build-v181/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__BALANCED_LIGHT_GREY_HALL_SURFACES_AND_BROAD_WALL_WASH_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V181_BUILD__NOT_PROMOTED",
    "source_map": BASE, "map": MAP,
    "changed_surface_count": len(changed),
    "roof_liner_count": roof_count,
    "hidden_superseded_visuals": sorted(hidden_superseded),
    "wall_wash_lights": wall_wash,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "coil_materials_or_transforms_changed": False,
    "agv_crane_navigation_or_gameplay_authority_changed": False,
    "protected_v180_sha256_before": base_hash_before,
    "protected_v180_sha256_after": base_hash_after,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "changed": len(changed), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
