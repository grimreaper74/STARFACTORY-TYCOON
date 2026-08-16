"""Build RP01 dock core v002 as a fabricated-detail successor of v001."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy


def load_builder(path: Path):
    spec = importlib.util.spec_from_file_location("lb_rp01_dock_core_v001_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output .blend path required")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    builder_path = Path(__file__).with_name("build_rp01_dock_core_candidate_v001.py")
    builder = load_builder(builder_path)
    saved_argv = list(sys.argv)
    try:
        sys.argv = [str(builder_path), "--", str(output)]
        builder.main()
    finally:
        sys.argv = saved_argv

    shared = bpy.data.collections["LB_RP01_DOCK_SHARED"]
    root = bpy.data.objects["ROOT_LB_RP01_DOCK_CORE_V001"]
    root.name = "ROOT_LB_RP01_DOCK_CORE_V002"
    root["lb_status"] = "FABRICATED_DETAIL_SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_source_parent"] = "algorithmic successor of immutable v001"
    root["lb_authority_change"] = "NONE_PRESENTATION_DETAIL_ONLY"
    charcoal = bpy.data.materials["M_CA_RP01_Dock_Charcoal"]
    graphite = bpy.data.materials["M_CA_RP01_Dock_Graphite"]
    green = bpy.data.materials["M_CA_RP01_Dock_CairnwellGreen"]
    yellow = bpy.data.materials["M_CA_RP01_Dock_SafetyYellow"]
    steel = bpy.data.materials["M_CA_RP01_Dock_BrushedSteel"]
    rubber = bpy.data.materials["M_CA_RP01_Dock_Rubber"]
    white = bpy.data.materials["M_CA_RP01_Dock_Label"]
    lamp = builder.material("M_CA_RP01_Dock_ServiceLamp", (0.72, 0.86, 0.95, 1.0), 0.1, 0.2)

    def part(name, length, width, height, x, y, z, mat=graphite, bevel=5):
        obj = builder.box(name, length, width, height, x, y, z, shared, mat, bevel)
        obj.parent = root
        obj["lb_scope"] = "PRESENTATION_DETAIL_NO_NEW_AUTHORITY"
        return obj

    # Fabricated canopy begins just behind the vehicle envelope and stays within
    # the retained 1.7 m recommended MR dock envelope. The existing beacon is
    # intentionally left as the small highest item.
    part("SM_LB_RP01_DockCanopy", 1220, 2480, 78, -1435, 0, 1502, charcoal, 10)
    part("SM_LB_RP01_DockCanopyFrontFascia", 70, 2480, 155, -800, 0, 1458, green, 8)
    part("SM_LB_RP01_DockCanopyRearDripEdge", 45, 2520, 65, -2070, 0, 1470, steel, 5)
    for lateral in (-1185, 1185):
        part(f"SM_LB_RP01_DockSideFrame_{lateral:+.0f}", 1120, 92, 1320, -1450, lateral, 805, graphite, 10)
        part(f"SM_LB_RP01_DockSideLowerKick_{lateral:+.0f}", 1180, 120, 150, -1450, lateral, 215, yellow, 10)
    for x in (-1900, -1580, -1260, -940):
        part(f"SM_LB_RP01_DockCanopyRib_{x:+.0f}", 54, 2350, 72, x, 0, 1450, steel, 4)

    # Rear service doors, hinges, latches and pressed ventilation make the back
    # plane read as maintainable plant rather than a single slab.
    for side in (-1, 1):
        lateral = side * 570
        suffix = "L" if side < 0 else "R"
        part(f"SM_LB_RP01_DockRearServiceDoor_{suffix}", 28, 990, 1040, -1972, lateral, 800, graphite, 7)
        part(f"SM_LB_RP01_DockRearDoorLatch_{suffix}", 55, 42, 150, -1945, lateral - side * 395, 810, yellow, 4)
        for z in (430, 790, 1150):
            hinge = builder.cylinder(f"SM_LB_RP01_DockRearDoorHinge_{suffix}_{z}", 40, 70,
                                     -1940, side * 1085, z, "CFR_Z", shared, steel)
            hinge.parent = root
            hinge["lb_scope"] = "PRESENTATION_DETAIL_NO_NEW_AUTHORITY"
        for index in range(7):
            part(f"SM_LB_RP01_DockRearVent_{suffix}_{index + 1:02d}", 32, 330, 18,
                 -1942, lateral, 1030 + index * 38, rubber, 1)

    # Protected ceiling services and task lighting; no service rating is claimed.
    part("SM_LB_RP01_DockOverheadCableTray", 920, 180, 85, -1450, 930, 1395, steel, 5)
    for lateral in (-720, 0, 720):
        fixture = part(f"SM_LB_RP01_DockTaskLight_{lateral:+.0f}", 420, 120, 34,
                       -1200, lateral, 1438, lamp, 5)
        fixture["lb_runtime_light_output"] = "TBC_NOT_INVENTED"
    for lateral in (-1080, 1080):
        conduit = builder.cylinder(f"SM_LB_RP01_DockRoofConduit_{lateral:+.0f}", 34, 860,
                                   -1760, lateral, 1375, "CFR_X", shared, rubber)
        conduit.parent = root
        conduit["lb_scope"] = "PRESENTATION_DETAIL_NO_NEW_AUTHORITY"

    # Anchor plates, triangular-looking stacked gussets and replaceable corner wear.
    for x in (-2020, -880):
        for lateral in (-1210, 1210):
            part(f"SM_LB_RP01_DockAnchorPlate_{x:+.0f}_{lateral:+.0f}", 190, 190, 26,
                 x, lateral, 128, steel, 5)
            for offset in (0, 45):
                bolt = builder.cylinder(f"SM_LB_RP01_DockAnchorBolt_{x:+.0f}_{lateral:+.0f}_{offset}",
                                        28, 22, x + offset - 22, lateral, 150, "CFR_Z", shared, steel)
                bolt.parent = root
        for lateral in (-1120, 1120):
            part(f"SM_LB_RP01_DockGusset_{x:+.0f}_{lateral:+.0f}", 220, 42, 220,
                 x, lateral, 285, graphite, 4)

    # Restrained mounted family plate; variant identity remains on each dock.
    identity_plate = part("SM_LB_RP01_DockFamilyPlate", 24, 780, 150, -770, 0, 1580, green, 7)
    identity_plate["lb_branding"] = "CAIRNWELL AUTOMOTIVE | MOORCROSS WORKS"
    family_text = builder.label("TXT_LB_RP01_DockFamilyMounted", "AUTONOMOUS SERVICE DOCK",
                                -754, 0, 1580, 0.048, shared, white)
    family_text.parent = root

    bpy.context.scene["lb_candidate"] = "RP01_DOCK_CORE_V002"
    bpy.context.scene["lb_promotion_authorized"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved fabricated-detail shared core v002 {output}")


if __name__ == "__main__":
    main()
