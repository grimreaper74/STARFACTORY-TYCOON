"""Derive the release-direction shared press-train source v002 from v001.

The v001 dimensions and pivots remain authoritative.  This deterministic source
adapter replaces the cabinet-like side facade with an open guarded process bay,
integrated access platform/rail and stage HMI while retaining every envelope.
"""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_shared_source_v001.py")
code = base.read_text(encoding="utf-8")

old_side = '''    # Side service panels, glazing and proper yellow access edges.
    for side, sign in (("L", -1), ("R", 1)):
        panel_x = sign * (half_x - 130)
        door_x = sign * (half_x - 145)
        window_x = sign * (half_x - 19)
        edge_x = sign * (half_x - 55)
        parts.append(box(f"{prefix}_SidePanel_{side}", (260, length - 1600, height * 0.48), (panel_x, 0, height * 0.39), "CA_MW_ServiceGrey", bevel=24))
        parts.append(box(f"{prefix}_ServiceDoor_{side}", (290, 1500, 2350), (door_x, -900, 1450), "CA_MW_CairnwellGreen", bevel=24))
        parts.append(box(f"{prefix}_DoorWindow_{side}", (38, 900, 700), (window_x, -900, 1850), "CA_MW_InspectionGlass", bevel=18))
        parts.append(box(f"{prefix}_DoorEdge_{side}", (110, 1700, 120), (edge_x, -900, 2580), "CA_MW_SafetyYellow", bevel=12))
'''

new_side = '''    # CCTV/service side (-X): open guarded process bay rather than a monolithic
    # cabinet panel.  The lower die, bolster, slide guides and crown remain visible
    # while genuine access protection and a remote-status HMI communicate scale.
    camera_x = -half_x + 130
    parts.extend([
        box(f"{prefix}_CameraSideLowerSkirt", (260, length - 1200, 780), (camera_x, 0, 740), "CA_MW_FoundryCharcoal", bevel=24),
        box(f"{prefix}_CameraSideUpperFascia", (260, length - 1200, 1180), (camera_x, 0, height - 1720), "CA_MW_CairnwellGreen", bevel=35),
        box(f"{prefix}_CameraSideJambIn", (300, 900, height - 1900), (camera_x, -half_y + 760, (height - 1900) / 2 + 700), "CA_MW_FoundryCharcoal", bevel=28),
        box(f"{prefix}_CameraSideJambOut", (300, 900, height - 1900), (camera_x, half_y - 760, (height - 1900) / 2 + 700), "CA_MW_FoundryCharcoal", bevel=28),
        box(f"{prefix}_CameraSidePlatform", (1050, length - 1500, 160), (-half_x + 660, 0, 1280), "CA_MW_ServiceGrey", bevel=22),
        box(f"{prefix}_CameraSideRailTop", (110, length - 1750, 110), (-half_x + 115, 0, 2350), "CA_MW_SafetyYellow", bevel=18),
        box(f"{prefix}_CameraSideRailMid", (90, length - 1750, 90), (-half_x + 115, 0, 1870), "CA_MW_SafetyYellow", bevel=14),
        box(f"{prefix}_CameraSideToeBoard", (80, length - 1750, 240), (-half_x + 115, 0, 1420), "CA_MW_SafetyYellow", bevel=12),
    ])
    for rail_index, rail_y in enumerate((-half_y + 950, -half_y * 0.34, 0, half_y * 0.34, half_y - 950)):
        parts.append(box(f"{prefix}_CameraSideRailPost_{rail_index}", (120, 120, 1120), (-half_x + 115, rail_y, 1800), "CA_MW_SafetyYellow", bevel=16))
    # A restrained stage HMI/status stack sits on the outer portal jamb.
    parts.extend([
        box(f"{prefix}_StageHMIHousing", (180, 720, 1050), (-half_x + 130, -half_y + 1250, 2700), "CA_MW_FoundryCharcoal", bevel=42),
        box(f"{prefix}_StageHMIScreen", (35, 530, 430), (-half_x + 80, -half_y + 1250, 2820), "CA_MW_InspectionGlass", bevel=20),
        box(f"{prefix}_StageHMIAccent", (45, 580, 90), (-half_x + 80, -half_y + 1250, 2420), "CA_MW_TrainAAccent", bevel=12),
    ])

    # Die-change/service side (+X): segmented cabinets and an interlocked door;
    # there is no duplicated false process opening on the service spine side.
    service_x = half_x - 130
    parts.extend([
        box(f"{prefix}_ServiceSideLower", (260, length - 1200, 1150), (service_x, 0, 900), "CA_MW_FoundryCharcoal", bevel=24),
        box(f"{prefix}_ServiceSideUpper", (260, length - 1200, height * 0.34), (service_x, 0, height * 0.57), "CA_MW_ServiceGrey", bevel=24),
        box(f"{prefix}_ServiceDoor_R", (290, 1500, 2350), (half_x - 145, -900, 1450), "CA_MW_CairnwellGreen", bevel=24),
        box(f"{prefix}_DoorWindow_R", (38, 900, 700), (half_x - 19, -900, 1850), "CA_MW_InspectionGlass", bevel=18),
        box(f"{prefix}_DoorEdge_R", (110, 1700, 120), (half_x - 55, -900, 2580), "CA_MW_SafetyYellow", bevel=12),
    ])
'''

if old_side not in code:
    raise RuntimeError("v001 enclosure side-facade source block changed; refusing an unsafe derivation")
code = code.replace(old_side, new_side)
# Keep the authored shell 20 mm inside each side of the implementation envelope.
# The inherited joined-bevel evaluation adds a 20 mm measured span at exact limits;
# this inset makes the exported evaluated mesh dimensionally compliant.
code = code.replace("    half_x = width / 2\n    half_y = length / 2", "    width = width - 40\n    half_x = width / 2\n    half_y = length / 2")
code = code.replace("Blockout_v001", "Presentation_v002")
code = code.replace("_v001", "_v002")
code = code.replace("source-kit-v001", "source-kit-v002")
code = code.replace("SOURCE_V001", "SOURCE_V002")
code = code.replace("shared seven-stage press-train source kit", "shared seven-stage press-train presentation kit")
exec(compile(code, str(base) + "::presentation_v002", "exec"), globals(), globals())
