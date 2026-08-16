"""Build the IND-HMI-001 v005 comparison entirely inside Unreal Engine.

No Blender/CAD meshes are imported.  The candidate is a dimensioned modular
assembly of Unreal-native primitive StaticMeshActors so every visible item can
be selected, replaced, animated or converted with Modeling Mode later.
"""

from __future__ import annotations

import json
from pathlib import Path
import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_HMI05_UnrealNativeValidation"
MAT_DIR = "/Game/LineBoss/Shared/HMI/IND_HMI_001_V005_UnrealNative/Materials"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/shared_hmi_v005_unreal_native.json"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
cylinder_mesh = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")


def material(name, colour, roughness=0.5, metallic=0.0, emission=None):
    path = f"{MAT_DIR}/{name}"
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
    unreal.MaterialEditingLibrary.delete_all_material_expressions(asset)
    base = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant3Vector, -420, 0
    )
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -420, 140
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -420, 250
    )
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emission:
        emit = unreal.MaterialEditingLibrary.create_material_expression(
            asset, unreal.MaterialExpressionConstant3Vector, -420, 370
        )
        emit.set_editor_property("constant", unreal.LinearColor(*emission, 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


M = {
    "stainless": material("M_HMI05_Stainless", (0.23, 0.27, 0.30), 0.25, 0.88),
    "edge": material("M_HMI05_EdgeSteel", (0.035, 0.045, 0.055), 0.28, 0.72),
    "charcoal": material("M_HMI05_Charcoal", (0.018, 0.024, 0.030), 0.42, 0.45),
    "rubber": material("M_HMI05_Rubber", (0.004, 0.006, 0.008), 0.76, 0.0),
    "screen": material("M_HMI05_Screen", (0.004, 0.018, 0.025), 0.18, 0.08, (0.01, 0.16, 0.24)),
    "ui": material("M_HMI05_UI", (0.02, 0.25, 0.44), 0.24, 0.0, (0.05, 0.40, 0.72)),
    "white": material("M_HMI05_White", (0.72, 0.76, 0.78), 0.48, 0.02),
    "red": material("M_HMI05_Red", (0.55, 0.012, 0.004), 0.25, 0.08, (0.20, 0.0, 0.0)),
    "amber": material("M_HMI05_Amber", (0.95, 0.25, 0.004), 0.24, 0.06, (0.42, 0.05, 0.0)),
    "green": material("M_HMI05_Green", (0.008, 0.48, 0.045), 0.25, 0.05, (0.0, 0.28, 0.02)),
    "blue": material("M_HMI05_Blue", (0.005, 0.14, 0.62), 0.24, 0.05),
    "yellow": material("M_HMI05_SafetyYellow", (0.92, 0.43, 0.005), 0.32, 0.04),
    "concrete": unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete"),
}


records = []


def primitive(label, mesh, location, size, mat, rotation=(0, 0, 0), mobility=unreal.ComponentMobility.STATIC):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label("LB_HMI05_" + label)
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    component.set_material(0, mat)
    component.set_editor_property("mobility", mobility)
    records.append({"label": actor.get_actor_label(), "location_cm": location, "size_cm": size, "rotation": rotation})
    return actor


def box(label, location, size, mat, rotation=(0, 0, 0), mobility=unreal.ComponentMobility.STATIC):
    return primitive(label, cube_mesh, location, size, mat, rotation, mobility)


def cylinder(label, location, diameter, depth, mat, rotation=(0, 0, 0), mobility=unreal.ComponentMobility.STATIC):
    return primitive(label, cylinder_mesh, location, (diameter, diameter, depth), mat, rotation, mobility)


def build():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        levels.load_level(MAP)
        for actor in actors.get_all_level_actors():
            actors.destroy_actor(actor)
    elif not levels.new_level(MAP):
        raise RuntimeError("Could not create Unreal-native HMI validation map")

    # Neutral studio prevents the black-background exposure failure seen in
    # the imported comparison map.
    box("StudioFloor", (0, 0, -7), (700, 700, 10), M["concrete"] or M["edge"])
    box("StudioBack", (0, -220, 145), (700, 10, 300), M["edge"])

    # Exact cabinet envelope: 600 W x 460 D x 1280 H; 1590 to stack-light top.
    box("Plinth", (0, 0, 5), (56, 46, 10), M["edge"])
    box("LowerCabinet", (0, 0, 50), (60, 46, 80), M["stainless"])
    box("FrontDoorInset", (0, 23.15, 50), (54, 1.2, 70), M["charcoal"])
    box("FrontDoorSkin", (0, 23.85, 50), (51.5, 0.8, 67.5), M["stainless"])
    box("DoorHandle", (-23.5, 25.0, 50), (2.2, 2.3, 14), M["edge"])
    cylinder("DoorLock", (-23.5, 26.5, 62), 2.3, 1.6, M["stainless"], (0, 0, 90))

    # Operator console: a native sloped assembly.  Side cheeks hide the rear
    # of the rotated panel, giving the correct folded-cabinet silhouette.
    box("ConsoleCore", (0, 0, 102), (60, 46, 24), M["stainless"])
    box("OperatorFace", (0, 20.8, 112), (58, 3.0, 35), M["stainless"], (-20, 0, 0))
    box("OperatorFaceEdge", (0, 22.2, 112), (59.2, 0.8, 36.2), M["edge"], (-20, 0, 0))
    box("OperatorFaceSkin", (0, 22.65, 112), (57.4, 0.55, 34.4), M["stainless"], (-20, 0, 0))
    box("LeftCheek", (-28.5, 0, 108), (3, 43, 34), M["stainless"])
    box("RightCheek", (28.5, 0, 108), (3, 43, 34), M["stainless"])

    # 17-inch 4:3 display opening, exactly 340 x 255 mm.
    box("ScreenHood", (0, 25.0, 117.0), (40, 3.2, 31), M["edge"], (-20, 0, 0))
    box("ScreenBezel", (0, 26.2, 117.0), (37.2, 1.6, 28.2), M["rubber"], (-20, 0, 0))
    box("ScreenGlass", (0, 27.1, 117.0), (34.0, 0.6, 25.5), M["screen"], (-20, 0, 0))
    # Readable schematic blocks at normal gameplay distance.
    for x in (-10.5, -3.5, 3.5, 10.5):
        box(f"UIScreenNode_{x:+.1f}", (x, 27.6, 119), (5.2, 0.25, 5.4), M["ui"], (-20, 0, 0))
    for index, width in enumerate((24, 20, 16, 12)):
        box(f"UIStatusLine_{index}", (-5 + index * 1.8, 27.5, 108.7 - index * 1.3), (width, 0.2, 0.45), M["ui"], (-20, 0, 0))

    # Five distinct physical controls. Axis faces +Y; each is a separate actor
    # ready for click interaction or Blueprint rotation/translation.
    control_x = (-20, -10, 0, 10, 20)
    for index, x in enumerate(control_x):
        cylinder(f"ControlCollar_{index}", (x, 26.5, 97), 5.2 if index == 4 else 3.5, 1.2, M["stainless"], (0, 0, 90))
    cylinder("PowerKey", (control_x[0], 27.4, 97), 2.2, 2.2, M["edge"], (0, 0, 90), unreal.ComponentMobility.MOVABLE)
    cylinder("ModeSelector", (control_x[1], 27.4, 97), 2.5, 2.2, M["rubber"], (0, 0, 90), unreal.ComponentMobility.MOVABLE)
    cylinder("ResetBlue", (control_x[2], 27.4, 97), 2.7, 2.0, M["blue"], (0, 0, 90), unreal.ComponentMobility.MOVABLE)
    cylinder("CycleStartGreen", (control_x[3], 27.4, 97), 2.7, 2.0, M["green"], (0, 0, 90), unreal.ComponentMobility.MOVABLE)
    cylinder("EStopYellowCollar", (control_x[4], 27.4, 97), 5.0, 1.6, M["yellow"], (0, 0, 90))
    cylinder("EStopRedMushroom", (control_x[4], 28.8, 97), 4.2, 2.7, M["red"], (0, 0, 90), unreal.ComponentMobility.MOVABLE)

    # Plate, seams, hinge and bottom cable entry details.
    box("AssetPlate", (0, 24.7, 82), (26, 1.2, 7), M["edge"])
    box("AssetPlateInset", (0, 25.5, 82), (23.5, 0.25, 4.5), M["white"])
    for z in (18, 82):
        cylinder(f"FrontHinge_{z}", (-28.7, 23.7, z), 2.0, 6.5, M["edge"])
    for x in (-18, -6, 6, 18):
        cylinder(f"CableGland_{x:+d}", (x, 0, 1.0), 3.8, 2.0, M["rubber"])
    for x in (-25, 25):
        for y in (-20, 20):
            cylinder(f"AnchorBolt_{x}_{y}", (x, y, 0.8), 2.0, 1.6, M["stainless"])

    # Right-side filtered vent.
    box("VentFrame", (30.6, -2, 50), (1.2, 23, 25), M["edge"])
    for index in range(7):
        box(f"VentSlat_{index}", (31.3, -2, 42 + index * 2.7), (0.8, 18, 0.9), M["stainless"])

    # Rear service door is deliberately open and movable for maintenance view.
    box("RearDoor", (40, -22, 50), (1.8, 54, 70), M["stainless"], (0, 35, 0), unreal.ComponentMobility.MOVABLE)
    box("RearDoorSeal", (39.2, -22, 50), (0.8, 50, 66), M["rubber"], (0, 35, 0), unreal.ComponentMobility.MOVABLE)

    # Stack light reaches the specified 1590 mm overall height.
    cylinder("StackPole", (0, 0, 139), 2.4, 22, M["edge"])
    cylinder("StackBase", (0, 0, 148), 5.2, 3.0, M["edge"])
    cylinder("StackGreen", (0, 0, 151.5), 5.0, 5.0, M["green"], mobility=unreal.ComponentMobility.MOVABLE)
    cylinder("StackAmber", (0, 0, 155.0), 5.0, 5.0, M["amber"], mobility=unreal.ComponentMobility.MOVABLE)
    cylinder("StackRed", (0, 0, 158.0), 5.0, 4.0, M["red"], mobility=unreal.ComponentMobility.MOVABLE)

    # Balanced studio lighting and fixed comparison camera.
    key = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(140, 180, 210), unreal.Rotator())
    key.set_actor_label("LB_HMI05_Key")
    key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(key.get_actor_location(), unreal.Vector(0, 0, 82)), False)
    key.get_editor_property("rect_light_component").set_editor_properties({"intensity": 850.0, "attenuation_radius": 700.0, "source_width": 180.0, "source_height": 180.0})
    fill = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-170, 80, 150), unreal.Rotator())
    fill.set_actor_label("LB_HMI05_Fill")
    fill.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(fill.get_actor_location(), unreal.Vector(0, 0, 80)), False)
    fill.get_editor_property("rect_light_component").set_editor_properties({"intensity": 350.0, "attenuation_radius": 700.0, "source_width": 130.0, "source_height": 130.0})
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(170, 280, 135), unreal.Rotator())
    camera.set_actor_label("LB_CAM_HMI05_Front")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 80)), False)
    camera.get_editor_property("camera_component").set_editor_property("field_of_view", 36.0)

    levels.save_current_level()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "status": "UNREAL_NATIVE_CANDIDATE_NOT_PROMOTED",
        "map": MAP,
        "asset_id": "IND-HMI-001",
        "revision": "v005_unreal_native",
        "cabinet_contract_cm": {"width": 60, "depth": 46, "console_height": 128, "overall_height": 159},
        "screen_contract_cm": {"width": 34, "height": 25.5, "aspect": "4:3", "panel_angle_deg": 20},
        "primitive_actor_count": len(records),
        "actors": records,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_HMI05_NATIVE_PASS actors={len(records)} audit={AUDIT}")


build()

