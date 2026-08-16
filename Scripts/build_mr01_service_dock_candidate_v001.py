"""Build the MR01 service/tool dock around the linked RP01 common dock core."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy


MM = 0.001


def cfr(x_mm: float, y_mm: float, z_mm: float) -> tuple[float, float, float]:
    return (y_mm * MM, -x_mm * MM, z_mm * MM)


def cfr_dims(length_mm: float, width_mm: float, height_mm: float) -> tuple[float, float, float]:
    return (width_mm * MM, length_mm * MM, height_mm * MM)


def collection(name: str) -> bpy.types.Collection:
    result = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if result.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(result)
    return result


def move_to(obj: bpy.types.Object, target: bpy.types.Collection) -> None:
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    target.objects.link(obj)


def material(name: str, rgba: tuple[float, float, float, float], metallic: float, roughness: float) -> bpy.types.Material:
    result = bpy.data.materials.new(name)
    result.diffuse_color = rgba
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return result


def box(name: str, length: float, width: float, height: float, x: float, y: float, z: float,
        target: bpy.types.Collection, mat: bpy.types.Material, bevel_mm: float = 0.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=cfr(x, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = cfr_dims(length, width, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_mm:
        modifier = obj.modifiers.new("EdgeBreak", "BEVEL")
        modifier.width = bevel_mm * MM
        modifier.segments = 2
    obj.data.materials.append(mat)
    move_to(obj, target)
    return obj


def cylinder(name: str, diameter: float, depth: float, x: float, y: float, z: float,
             axis: str, target: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    rotation = (0.0, 0.0, 0.0)
    if axis == "CFR_X":
        rotation = (math.radians(90), 0.0, 0.0)
    elif axis == "CFR_Y":
        rotation = (0.0, math.radians(90), 0.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=diameter * MM * 0.5, depth=depth * MM,
                                       location=cfr(x, y, z), rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    move_to(obj, target)
    return obj


def empty(name: str, x: float, y: float, z: float, target: bpy.types.Collection,
          axis: str, movement: str) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.1
    obj.location = cfr(x, y, z)
    obj["lb_coordinate_frame"] = "CFR"
    obj["lb_cfr_mm"] = f"{x},{y},{z}"
    obj["lb_axis"] = axis
    obj["lb_movement"] = movement
    target.objects.link(obj)
    return obj


def label(name: str, body: str, x: float, y: float, z: float, size: float,
          target: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_Curve", "FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.003
    obj = bpy.data.objects.new(name, curve)
    obj.location = cfr(x, y, z)
    obj.rotation_euler = (math.radians(90), 0.0, 0.0)
    obj.data.materials.append(mat)
    target.objects.link(obj)
    return obj


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- shared_core.blend output.blend")
    shared_path = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 1.0

    with bpy.data.libraries.load(str(shared_path), link=True) as (source, target):
        required_shared_collections = ["LB_RP01_DOCK_SHARED", "LB_RP01_DOCK_SOCKETS"]
        missing = [name for name in required_shared_collections if name not in source.collections]
        if missing:
            raise RuntimeError(f"Shared dock collections missing: {missing}")
        target.collections = required_shared_collections
    for linked_collection in target.collections:
        scene.collection.children.link(linked_collection)

    static = collection("30_LB_MR01_DOCK_STATIC")
    moving = collection("31_LB_MR01_DOCK_MOVING")
    tools = collection("32_LB_MR01_DOCK_TOOLS")
    pivots = collection("50_LB_MR01_DOCK_SOCKETS_PIVOTS")
    reference = collection("90_LB_MR01_DOCK_REFERENCE")

    graphite = material("M_CA_MR01_Dock_Graphite", (0.06, 0.07, 0.075, 1.0), 0.58, 0.42)
    green = material("M_CA_MR01_Dock_CairnwellGreen", (0.06, 0.16, 0.105, 1.0), 0.35, 0.48)
    yellow = material("M_CA_MR01_Dock_SafetyYellow", (0.92, 0.52, 0.025, 1.0), 0.25, 0.42)
    steel = material("M_CA_MR01_Dock_ToolSteel", (0.26, 0.29, 0.3, 1.0), 0.82, 0.27)
    rubber = material("M_CA_MR01_Dock_Rubber", (0.008, 0.012, 0.014, 1.0), 0.0, 0.82)
    white = material("M_CA_MR01_Dock_Label", (0.76, 0.82, 0.78, 1.0), 0.0, 0.38)
    orange = material("M_CA_MR01_Dock_WasteOrange", (0.8, 0.19, 0.02, 1.0), 0.1, 0.46)
    fluid = material("M_CA_MR01_Dock_FluidBlue", (0.01, 0.18, 0.4, 1.0), 0.25, 0.3)

    root = bpy.data.objects.new("ROOT_LB_MR01_SERVICE_DOCK_V001", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.35
    static.objects.link(root)
    root["lb_status"] = "SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_shared_library"] = str(shared_path)
    root["lb_dock_envelope_mm"] = "2600x1400x1700"

    calibration_pivot = empty("PVT_DockCalibrationProbe", -900, 0, 950, pivots, "CFR_X", "0..180 mm")
    calibration_pivot.parent = root
    rack_door_pivot = empty("PVT_DockToolRackDoor", -1000, 500, 900, pivots, "CFR_Z", "0..100 deg")
    rack_door_pivot.parent = root
    waste_drawer_pivot = empty("PVT_DockWasteDrawer", -900, -500, 420, pivots, "CFR_Y", "0..-450 mm")
    waste_drawer_pivot.parent = root

    def parent_preserve_world(obj: bpy.types.Object, parent: bpy.types.Object) -> None:
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world

    # MR01-only side modules stay outside the 930 mm robot travel envelope.
    box("SM_LB_MR01_DockConsumablesCabinet", 720, 590, 1180, -1600, -925, 760, static, green, 22).parent = root
    box("SM_LB_MR01_DockConsumablesDoor", 20, 500, 1000, -1215, -925, 760, moving, green, 12).parent = root
    box("SM_LB_MR01_DockToolRackCabinet", 720, 590, 1180, -1600, 925, 760, static, graphite, 22).parent = root
    rack_door = box("SM_LB_MR01_DockToolRackDoor", 24, 520, 1040, -1210, 925, 900, moving, green, 10)
    parent_preserve_world(rack_door, rack_door_pivot)
    rack_door["lb_pivot_authority"] = "PVT_DockToolRackDoor"
    rack_door["lb_range"] = "0..100 deg about CFR Z"

    # Exact eight-position rack: two columns by four rows, no extra slots.
    tool_names = [
        "T1_InspectionHead", "T2_ConditionProbe", "T3_LubricationTool", "T4_CleaningTool",
        "T5_ServiceGripper", "T6_TorqueTool", "T7_FluidLeakTool", "T8_ModuleExchangeTool",
    ]
    for index, tool_name in enumerate(tool_names):
        column = index % 2
        row = index // 2
        lateral = 790 + column * 250
        z = 1240 - row * 235
        box(f"SM_LB_MR01_DockToolCradle_{index + 1:02d}", 300, 205, 70, -1610, lateral, z - 115,
            tools, yellow, 8).parent = root
        cylinder(f"SM_LB_MR01_{tool_name}", 82 + (index % 3) * 8, 260, -1610, lateral, z,
                 "CFR_Z", tools, steel).parent = root
        label(f"TXT_LB_MR01_Tool_{index + 1:02d}", f"T{index + 1}", -1220, lateral, z, 0.055,
              tools, white).parent = root

    # Calibration frame/probe at exact pivot, extending 180 mm along CFR X toward the robot.
    box("SM_LB_MR01_DockCalibrationFrame", 180, 580, 120, -990, 0, 1120, static, yellow, 14).parent = root
    box("SM_LB_MR01_DockCalibrationUpright_L", 160, 90, 720, -1050, -260, 870, static, graphite, 12).parent = root
    box("SM_LB_MR01_DockCalibrationUpright_R", 160, 90, 720, -1050, 260, 870, static, graphite, 12).parent = root
    probe = cylinder("SM_LB_MR01_DockCalibrationProbe", 70, 260, -900, 0, 950, "CFR_X", moving, steel)
    parent_preserve_world(probe, calibration_pivot)
    probe["lb_pivot_authority"] = "PVT_DockCalibrationProbe"
    probe["lb_travel"] = "180 mm along CFR X"

    # Consumables, parts lockers and waste drawer.
    for row in range(3):
        box(f"SM_LB_MR01_DockPartsLocker_{row + 1}", 190, 450, 230, -1760 + row * 250, -925, 1050,
            static, graphite, 10).parent = root
    for lateral, name, mat in ((-1040, "Grease", yellow), (-840, "Diagnostic", fluid)):
        cylinder(f"SM_LB_MR01_Dock{name}Service", 95, 340, -1380, lateral, 610, "CFR_Z", static, mat).parent = root
    waste = box("SM_LB_MR01_DockWasteDrawer", 520, 520, 230, -900, -500, 420, moving, graphite, 12)
    parent_preserve_world(waste, waste_drawer_pivot)
    waste["lb_pivot_authority"] = "PVT_DockWasteDrawer"
    waste["lb_travel"] = "450 mm along negative CFR Y"
    box("SM_LB_MR01_DockWasteDrawerInsert", 430, 430, 95, -900, -500, 470, moving, orange, 8).parent = waste

    # Spill/leak and service detailing.
    box("SM_LB_MR01_DockSpillTray", 1060, 1000, 36, -1435, 0, 150, static, steel, 8).parent = root
    box("SM_LB_MR01_DockLeakSensor", 90, 140, 55, -1080, -360, 195, static, orange, 6).parent = root
    for lateral in (-1080, 1080):
        cylinder(f"SM_LB_MR01_DockCableConduit_{lateral:+.0f}", 45, 980, -1810, lateral, 960,
                 "CFR_Z", static, rubber).parent = root

    label("TXT_LB_MR01_DockIdentity", "MR01 SERVICE / TOOL DOCK", -1210, 0, 1510, 0.075,
          static, white).parent = root
    label("TXT_LB_MR01_DockTBC", "CAIRNWELL AUTOMOTIVE  |  MOORCROSS WORKS", -1210, 0, 1435, 0.042,
          static, white).parent = root

    # Authoritative MR01-only pivots and useful gameplay sockets.
    empty("SCK_DockCalibrationProbe", -720, 0, 950, pivots, "CFR_X", "engaged endpoint").parent = root
    for index in range(8):
        column = index % 2
        row = index // 2
        empty(f"SCK_DockToolRack_{index + 1:02d}", -1610, 790 + column * 250, 1240 - row * 235,
              pivots, "CFR_X", f"tool T{index + 1}").parent = root

    # Wire reference envelope, excluded from rendering/export collections.
    envelope = box("REF_LB_MR01_DockEnvelope_2600x1400x1700", 1400, 2600, 1700, -1435, 0, 850,
                   reference, green, 0)
    envelope.display_type = "WIRE"
    envelope.hide_render = True
    envelope["lb_status"] = "RECOMMENDED_TBC_VALIDATION"
    approach = box("REF_LB_MR01_StraightApproach_3000", 3000, 1400, 50, 765, 0, 25,
                   reference, yellow, 0)
    approach.display_type = "WIRE"
    approach.hide_render = True

    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
