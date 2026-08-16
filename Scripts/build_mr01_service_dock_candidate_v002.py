"""Build MR01 dock v002 as a non-overwriting visual-detail successor of v001."""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import bpy


def load_builder(path: Path):
    spec = importlib.util.spec_from_file_location("lb_mr01_dock_v001_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_object(name: str) -> None:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- shared_core.blend output_v002.blend")
    shared_path = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    builder_path = Path(__file__).with_name("build_mr01_service_dock_candidate_v001.py")
    builder = load_builder(builder_path)
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(builder_path), "--", str(shared_path), str(output)]
        builder.main()
    finally:
        sys.argv = saved_argv

    static = bpy.data.collections["30_LB_MR01_DOCK_STATIC"]
    tools = bpy.data.collections["32_LB_MR01_DOCK_TOOLS"]
    graphite = bpy.data.materials["M_CA_MR01_Dock_Graphite"]
    green = bpy.data.materials["M_CA_MR01_Dock_CairnwellGreen"]
    yellow = bpy.data.materials["M_CA_MR01_Dock_SafetyYellow"]
    steel = bpy.data.materials["M_CA_MR01_Dock_ToolSteel"]
    rubber = bpy.data.materials["M_CA_MR01_Dock_Rubber"]
    white = bpy.data.materials["M_CA_MR01_Dock_Label"]
    orange = bpy.data.materials["M_CA_MR01_Dock_WasteOrange"]
    fluid = bpy.data.materials["M_CA_MR01_Dock_FluidBlue"]
    root = bpy.data.objects["ROOT_LB_MR01_SERVICE_DOCK_V001"]
    root.name = "ROOT_LB_MR01_SERVICE_DOCK_V002"
    root["lb_status"] = "SOURCE_CANDIDATE_V002_NOT_PROMOTED"
    root["lb_source_parent"] = "algorithmic successor of v001; v001 blend remains immutable"
    root["lb_visual_revision"] = "open fabricated cabinets; visible eight-tool rack; mounted identity; service detailing"

    # Remove the visually rejected solid volumes and floating labels. Exact moving
    # pivots, sockets, base, tools and linked shared core remain untouched.
    for name in (
        "SM_LB_MR01_DockConsumablesCabinet",
        "SM_LB_MR01_DockConsumablesDoor",
        "SM_LB_MR01_DockToolRackCabinet",
        "TXT_LB_MR01_DockIdentity",
        "TXT_LB_MR01_DockTBC",
    ):
        remove_object(name)
    for index in range(1, 9):
        remove_object(f"TXT_LB_MR01_Tool_{index:02d}")

    def part(name, length, width, height, x, y, z, target=static, mat=graphite, bevel=4):
        obj = builder.box(name, length, width, height, x, y, z, target, mat, bevel)
        obj.parent = root
        return obj

    # Open, fabricated five-panel tool cabinet. The front is intentionally open
    # behind the authoritative hinged door so all eight tools are physically visible.
    part("SM_LB_MR01_ToolRack_BackPanel", 28, 590, 1180, -1946, 925, 760, mat=graphite, bevel=3)
    part("SM_LB_MR01_ToolRack_Side_L", 720, 28, 1180, -1600, 644, 760, mat=graphite, bevel=3)
    part("SM_LB_MR01_ToolRack_Side_R", 720, 28, 1180, -1600, 1206, 760, mat=graphite, bevel=3)
    part("SM_LB_MR01_ToolRack_Top", 720, 590, 32, -1600, 925, 1334, mat=green, bevel=4)
    part("SM_LB_MR01_ToolRack_Sill", 720, 590, 48, -1600, 925, 194, mat=yellow, bevel=5)
    part("SM_LB_MR01_ToolRack_Divider", 640, 22, 1050, -1600, 915, 750, mat=steel, bevel=2)
    for row in range(5):
        part(f"SM_LB_MR01_ToolRack_Rail_{row + 1:02d}", 42, 520, 34, -1912, 925,
             305 + row * 230, mat=steel, bevel=2)

    # Re-mount T1-T8 identity plates on the rack back rather than floating in front.
    for index in range(8):
        column = index % 2
        row = index // 2
        lateral = 790 + column * 250
        z = 1240 - row * 235
        plate = part(f"SM_LB_MR01_ToolPlaque_{index + 1:02d}", 18, 118, 58, -1922, lateral,
                     z + 74, target=tools, mat=green, bevel=3)
        plate["lb_tool_id"] = f"T{index + 1}"
        text = builder.label(f"TXT_LB_MR01_ToolMounted_{index + 1:02d}", f"T{index + 1}",
                             -1908, lateral, z + 74, 0.042, tools, white)
        text.parent = root

    # Open fabricated consumables/service cabinet. Its service hardware remains
    # fixed presentation because no additional moving-pivot authority was supplied.
    part("SM_LB_MR01_Consumables_BackPanel", 28, 590, 1180, -1946, -925, 760, mat=green, bevel=3)
    part("SM_LB_MR01_Consumables_Side_L", 720, 28, 1180, -1600, -1206, 760, mat=green, bevel=3)
    part("SM_LB_MR01_Consumables_Side_R", 720, 28, 1180, -1600, -644, 760, mat=green, bevel=3)
    part("SM_LB_MR01_Consumables_Top", 720, 590, 32, -1600, -925, 1334, mat=green, bevel=4)
    part("SM_LB_MR01_Consumables_Sill", 720, 590, 48, -1600, -925, 194, mat=yellow, bevel=5)
    for row in range(4):
        part(f"SM_LB_MR01_Consumables_Shelf_{row + 1:02d}", 620, 530, 24, -1600, -925,
             330 + row * 245, mat=steel, bevel=2)
    for index, (lateral, z, mat) in enumerate((
        (-1050, 435, fluid), (-805, 435, yellow), (-1050, 680, steel), (-805, 680, orange),
        (-1050, 925, yellow), (-805, 925, fluid), (-1050, 1170, steel), (-805, 1170, green),
    ), start=1):
        module = part(f"SM_LB_MR01_ConsumableModule_{index:02d}", 300, 170, 150, -1575,
                      lateral, z, mat=mat, bevel=10)
        module["lb_service_data"] = "TBC_NOT_INVENTED"

    # Fabrication cues: door hinges/latch, vents, cable tray, protected hoses,
    # fasteners and wear rails. These are presentation detail, not new authority.
    for z in (500, 900, 1250):
        hinge = builder.cylinder(f"SM_LB_MR01_ToolDoorHinge_{z}", 48, 82, -1218, 650, z,
                                 "CFR_Z", static, steel)
        hinge.parent = root
    part("SM_LB_MR01_ToolDoorLatch", 65, 40, 155, -1192, 1165, 895, mat=yellow, bevel=5)
    for index in range(6):
        part(f"SM_LB_MR01_ConsumablesVent_{index + 1:02d}", 22, 310, 18, -1203, -925,
             1080 + index * 32, mat=rubber, bevel=1)
    part("SM_LB_MR01_RearCableTray", 70, 2240, 65, -1880, 0, 1420, mat=steel, bevel=6)
    for lateral, mat in ((-1130, fluid), (-1060, yellow), (1060, orange), (1130, fluid)):
        hose = builder.cylinder(f"SM_LB_MR01_ProtectedServiceHose_{lateral:+.0f}", 32, 860,
                                -1840, lateral, 850, "CFR_Z", static, mat)
        hose.parent = root
    for side in (-1, 1):
        lateral = side * 1245
        for z in (260, 560, 860, 1160):
            fastener = builder.cylinder(f"SM_LB_MR01_FrameFastener_{side:+d}_{z}", 28, 18,
                                        -1510, lateral, z, "CFR_Y", static, steel)
            fastener.parent = root
    part("SM_LB_MR01_WearRail_L", 1180, 54, 30, -1360, -570, 170, mat=steel, bevel=3)
    part("SM_LB_MR01_WearRail_R", 1180, 54, 30, -1360, 570, 170, mat=steel, bevel=3)

    # One physically mounted family identification plate and two restrained text lines.
    identity_plate = part("SM_LB_MR01_DockIdentityPlate", 26, 1100, 190, -1175, 0, 1490,
                          mat=green, bevel=8)
    identity_plate["lb_branding"] = "CAIRNWELL AUTOMOTIVE | MOORCROSS WORKS"
    identity = builder.label("TXT_LB_MR01_DockIdentityMounted", "MR01 SERVICE / TOOL DOCK",
                             -1158, 0, 1520, 0.062, static, white)
    identity.parent = root
    brand = builder.label("TXT_LB_MR01_DockBrandMounted", "CAIRNWELL AUTOMOTIVE  |  MOORCROSS WORKS",
                          -1158, 0, 1460, 0.032, static, white)
    brand.parent = root

    bpy.context.scene["lb_candidate"] = "MR01_SERVICE_DOCK_V002"
    bpy.context.scene["lb_promotion_authorized"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved refined v002 {output}")


if __name__ == "__main__":
    main()
