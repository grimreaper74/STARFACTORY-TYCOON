"""Build the clean Line Boss Press Shop foundation map in Unreal 5.8."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir())
LAYOUT_PATH = PROJECT_ROOT / "Content/LineBoss/Data/press_shop_layout_v001.json"
MAP_PATH = "/Game/LineBoss/Maps/LB_PressShop_Foundation"


def make_material(asset_name: str, colour: list[float], roughness: float = 0.82):
    path = "/Game/LineBoss/Materials"
    library = unreal.EditorAssetLibrary
    asset_path = f"{path}/{asset_name}"
    if library.does_asset_exist(asset_path):
        return library.load_asset(asset_path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(asset_name, path, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, 0)
    base.set_editor_property("constant", unreal.LinearColor(float(colour[0]), float(colour[1]), float(colour[2]), 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 170)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    library.save_loaded_asset(material)
    return material


def spawn_cube(label: str, location, size_cm, material=None):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    component = actor.static_mesh_component
    component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    actor.set_actor_scale3d(unreal.Vector(size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0))
    if material is not None:
        component.set_material(0, material)
    component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    return actor


def build():
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assets = unreal.EditorAssetLibrary
    if assets.does_asset_exist(MAP_PATH):
        level.load_level(MAP_PATH)
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in actor_subsystem.get_all_level_actors():
            actor_subsystem.destroy_actor(actor)
    else:
        if not level.new_level(MAP_PATH):
            raise RuntimeError(f"Could not create {MAP_PATH}")

    floor_mat = make_material("M_LB_FactoryConcrete", [0.105, 0.115, 0.125], 0.90)
    wall_mat = make_material("M_LB_ShellCharcoal", [0.055, 0.065, 0.075], 0.78)
    column_mat = make_material("M_LB_StructureSteel", [0.13, 0.15, 0.17], 0.64)
    yellow_mat = make_material("M_LB_SafetyYellow", [0.72, 0.39, 0.025], 0.58)

    spawn_cube("LB_PRESS_FinishedFloor", (0, 0, -15), (22000, 12000, 30), floor_mat)
    for zone in layout["zones"]:
        mat = make_material(f"M_LB_Zone_{zone['id']}", zone["colour"], 0.88)
        sx, sy = zone["size_cm"]
        x, y, z = zone["centre_cm"]
        spawn_cube(f"LB_ZONE_{zone['id']}", (x, y, z), (sx, sy, 4), mat)

    # 18 m tall perimeter, deliberately roofless for the management camera.
    spawn_cube("LB_PRESS_Wall_North", (0, -6000, 900), (22000, 30, 1800), wall_mat)
    spawn_cube("LB_PRESS_Wall_South", (0, 6000, 900), (22000, 30, 1800), wall_mat)
    spawn_cube("LB_PRESS_Wall_West", (-11000, 0, 900), (30, 12000, 1800), wall_mat)
    spawn_cube("LB_PRESS_Wall_East", (11000, 0, 900), (30, 12000, 1800), wall_mat)

    # Reusable structural grid: 20 m bays along length, 15 m across width.
    for x in range(-10000, 10001, 2000):
        for y in (-5250, -3750, -2250, -750, 750, 2250, 3750, 5250):
            spawn_cube(f"LB_PRESS_Column_{x}_{y}", (x, y, 900), (45, 45, 1800), column_mat)
    for y in (-5250, -3750, -2250, -750, 750, 2250, 3750, 5250):
        spawn_cube(f"LB_PRESS_RoofBeam_{y}", (0, y, 1760), (21600, 30, 55), column_mat)

    # Safety-colour datum bars make the full footprint immediately legible.
    spawn_cube("LB_PRESS_MaterialFlowDatum", (0, -5450, 8), (20400, 24, 8), yellow_mat)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    sun = actor_subsystem.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-48, -28, 0))
    sun.set_actor_label("LB_PRESS_DirectionalFill")
    sun_component = sun.get_editor_property("directional_light_component")
    sun_component.set_editor_property("intensity", 4.0)
    sun_component.set_editor_property("light_color", unreal.Color(232, 239, 255, 255))

    camera = actor_subsystem.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-15500, 14500, 17000), unreal.Rotator())
    camera.set_actor_label("LB_CAM_PressShop_ManagementOverview")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 0)), False)
    camera.camera_component.set_editor_property("field_of_view", 48.0)

    top_camera = actor_subsystem.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, 0, 26000), unreal.Rotator())
    top_camera.set_actor_label("LB_CAM_PressShop_TopDown")
    top_camera.set_actor_rotation(unreal.Rotator(90.0, -90.0, 0.0), False)
    top_camera.camera_component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    top_camera.camera_component.set_editor_property("ortho_width", 25000.0)

    if not level.save_current_level():
        raise RuntimeError("Failed to save Press Shop foundation map")
    unreal.log("LINE_BOSS_PRESS_SHOP_FOUNDATION_PASS")


build()
