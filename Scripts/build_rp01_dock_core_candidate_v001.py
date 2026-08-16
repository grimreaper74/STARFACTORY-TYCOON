"""Build a modular RP01 common service-dock core in Blender 5.2.

The dock is authored in the docked robot CFR: robot centre at the origin,
CFR +X forward -> Blender -Y, CFR +Y right -> Blender +X, CFR +Z -> Blender +Z.
"""
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
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=diameter * MM * 0.5,
        depth=depth * MM,
        location=cfr(x, y, z),
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    move_to(obj, target)
    return obj


def socket(name: str, x: float, y: float, z: float, target: bpy.types.Collection, scope: str) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.08
    obj.location = cfr(x, y, z)
    obj["lb_coordinate_frame"] = "CFR"
    obj["lb_scope"] = scope
    obj["lb_cfr_mm"] = f"{x},{y},{z}"
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
    if not args:
        raise SystemExit("Output .blend path required")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 1.0

    shared = collection("LB_RP01_DOCK_SHARED")
    pivots = collection("LB_RP01_DOCK_SOCKETS")

    charcoal = material("M_CA_RP01_Dock_Charcoal", (0.035, 0.045, 0.05, 1.0), 0.65, 0.38)
    graphite = material("M_CA_RP01_Dock_Graphite", (0.075, 0.085, 0.09, 1.0), 0.5, 0.48)
    green = material("M_CA_RP01_Dock_CairnwellGreen", (0.075, 0.18, 0.12, 1.0), 0.3, 0.48)
    yellow = material("M_CA_RP01_Dock_SafetyYellow", (0.92, 0.52, 0.025, 1.0), 0.25, 0.42)
    steel = material("M_CA_RP01_Dock_BrushedSteel", (0.28, 0.31, 0.32, 1.0), 0.8, 0.28)
    rubber = material("M_CA_RP01_Dock_Rubber", (0.008, 0.012, 0.014, 1.0), 0.0, 0.82)
    red = material("M_CA_RP01_Dock_EStopRed", (0.55, 0.012, 0.008, 1.0), 0.05, 0.32)
    amber = material("M_CA_RP01_Dock_AmberLens", (1.0, 0.28, 0.01, 1.0), 0.0, 0.2)
    status_green = material("M_CA_RP01_Dock_GreenLens", (0.01, 0.65, 0.08, 1.0), 0.0, 0.2)
    white = material("M_CA_RP01_Dock_Label", (0.75, 0.82, 0.78, 1.0), 0.0, 0.38)

    root = bpy.data.objects.new("ROOT_LB_RP01_DOCK_CORE_V001", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.3
    shared.objects.link(root)
    root["lb_status"] = "CANDIDATE_NOT_PROMOTED"
    root["lb_design_envelope_mm"] = "2600x1400x1700"
    root["lb_coordinate_frame"] = "DOCKED_ROBOT_CFR"

    # Base spans CFR X -735 to -2135: 1400 mm dock depth behind the interface.
    box("SM_LB_RP01_DockBase", 1400, 2600, 110, -1435, 0, 55, shared, charcoal, 18).parent = root
    box("SM_LB_RP01_DockContainmentTray", 1240, 2380, 35, -1435, 0, 132, shared, graphite, 8).parent = root
    for lateral in (-1210, 1210):
        box(f"SM_LB_RP01_DockPost_{lateral:+.0f}", 160, 120, 1560, -2025, lateral, 880, shared, graphite, 16).parent = root
    for lateral in (-1200, 1200):
        box(f"SM_LB_RP01_DockFrontBumper_{lateral:+.0f}", 360, 180, 160, -900, lateral, 120, shared, yellow, 20).parent = root
    for lateral in (-1180, 1180):
        box(f"SM_LB_RP01_DockGuideRail_{lateral:+.0f}", 760, 120, 85, -1120, lateral, 165, shared, graphite, 14).parent = root
    box("SM_LB_RP01_DockStructuralSpine", 170, 2520, 220, -2040, 0, 1585, shared, charcoal, 16).parent = root
    box("SM_LB_RP01_DockRearPanel", 120, 2360, 1240, -2045, 0, 800, shared, graphite, 12).parent = root

    # Shared protected common interface at the exact MR01/RP01 CFR sockets.
    box("SM_LB_RP01_DockInterfaceGuard", 150, 720, 470, -840, 0, 420, shared, charcoal, 14).parent = root
    box("SM_LB_RP01_DockAlignmentBeam", 150, 520, 120, -785, 0, 250, shared, graphite, 12).parent = root
    for lateral in (-120, 120):
        cylinder(f"SM_LB_RP01_DockChargeContact_{lateral:+.0f}", 54, 70, -735, lateral, 340, "CFR_X", shared, steel).parent = root
        cylinder(f"SM_LB_RP01_DockAlignmentGuide_{lateral:+.0f}", 92, 145, -805, lateral, 250, "CFR_X", shared, yellow).parent = root
    cylinder("SM_LB_RP01_DockNetworkContact", 46, 72, -735, 0, 390, "CFR_X", shared, green).parent = root
    box("SM_LB_RP01_DockDatumPlate", 35, 180, 150, -752, 0, 310, shared, steel, 5).parent = root

    # Shared left service/isolation module and right diagnostics panel.
    box("SM_LB_RP01_DockIsolationCabinet", 520, 500, 1080, -1610, -980, 720, shared, green, 20).parent = root
    box("SM_LB_RP01_DockIsolationDoor", 16, 420, 900, -1325, -980, 720, shared, green, 10).parent = root
    box("SM_LB_RP01_DockDiagnosticsPanel", 95, 320, 600, -930, 960, 650, shared, graphite, 12).parent = root
    cylinder("SM_LB_RP01_DockEStop", 90, 45, -870, 960, 760, "CFR_X", shared, red).parent = root
    box("SM_LB_RP01_DockServiceHMI", 55, 180, 250, -850, 960, 1010, shared, charcoal, 8).parent = root

    # Common status beacon, fork pockets and lifting points.
    box("SM_LB_RP01_DockBeaconMast", 100, 100, 100, -2035, 1050, 1550, shared, graphite, 8).parent = root
    for index, (z, mat) in enumerate(((1620, status_green), (1650, amber), (1680, red))):
        cylinder(f"SM_LB_RP01_DockStackLight_{index}", 70, 54, -2035, 1050, z, "CFR_Z", shared, mat).parent = root
    for lateral in (-740, 740):
        box(f"SM_LB_RP01_DockForkPocket_{lateral:+.0f}", 390, 220, 85, -1540, lateral, 80, shared, rubber, 6).parent = root
    for lateral in (-1110, 1110):
        cylinder(f"SM_LB_RP01_DockLiftEye_{lateral:+.0f}", 100, 32, -2025, lateral, 1540, "CFR_Y", shared, yellow).parent = root

    label("TXT_LB_RP01_Dock_Cairnwell", "CAIRNWELL", -1330, 0, 1648, 0.10, shared, white).parent = root
    label("TXT_LB_RP01_Dock_Moorcross", "MOORCROSS WORKS", -1330, 0, 1575, 0.048, shared, white).parent = root

    for name, xyz in {
        "SCK_DockDatum": (-735, 0, 310),
        "SCK_ChargeContact_L": (-735, -120, 340),
        "SCK_ChargeContact_R": (-735, 120, 340),
        "SCK_NetworkContact": (-735, 0, 390),
    }.items():
        socket(name, *xyz, pivots, "EXACT_SHARED").parent = root

    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
