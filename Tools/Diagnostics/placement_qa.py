"""Placement QA: overlaps, floaters and sinkers, per shop region.

Wishlist-day bar: store screenshots come from the live map, so nothing
may interpenetrate, float or sink. Spatial-hashed pairwise bounds test
across the placed machine actors (same-mesh neighbours excluded - skid
chains and deck plates touch by design), plus base-height checks.
Writes the offender list for fix scripts.
"""
import json
import re
from collections import defaultdict

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_placement_qa.json"
PREFIXES = ("WeldLine_", "AsmLine_", "PaintLine_", "SignalKit_",
            "Site_Intake_", "Site_Transporter_", "Site_Veg_",
            "SkilletPlate_")
CELL = 800.0

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

actors = []
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    if not any(label.startswith(p) for p in PREFIXES):
        continue
    mesh_name = ""
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            mesh_name = mesh.get_name()
            break
    origin, extent = actor.get_actor_bounds(False)
    actors.append({
        "label": label, "mesh": mesh_name,
        "min": (origin.x - extent.x, origin.y - extent.y,
                origin.z - extent.z),
        "max": (origin.x + extent.x, origin.y + extent.y,
                origin.z + extent.z),
    })

grid = defaultdict(list)
for index, entry in enumerate(actors):
    gx0 = int(entry["min"][0] // CELL)
    gx1 = int(entry["max"][0] // CELL)
    gy0 = int(entry["min"][1] // CELL)
    gy1 = int(entry["max"][1] // CELL)
    for gx in range(gx0, gx1 + 1):
        for gy in range(gy0, gy1 + 1):
            grid[(gx, gy)].append(index)

def overlap_volume(a, b):
    dims = []
    for axis in range(3):
        lo = max(a["min"][axis], b["min"][axis])
        hi = min(a["max"][axis], b["max"][axis])
        if hi - lo <= 0.0:
            return 0.0
        dims.append(hi - lo)
    return dims[0] * dims[1] * dims[2]

seen = set()
overlaps = []
for bucket in grid.values():
    for i in range(len(bucket)):
        for j in range(i + 1, len(bucket)):
            a_i, b_i = bucket[i], bucket[j]
            key = (min(a_i, b_i), max(a_i, b_i))
            if key in seen:
                continue
            seen.add(key)
            a, b = actors[a_i], actors[b_i]
            if a["mesh"] == b["mesh"]:
                continue
            # Tunnel machines straddle the conveyor by design.
            straddlers = ("WaterLeakTestBooth", "FlashGantry",
                          "EOLInspectionArch", "PowertrainMarriage",
                          "HeavyMarriageGantry", "BodyLowerator",
                          "QualityLightTunnel", "FlashOffTunnel",
                          "VisionGate", "OverheadDropLift",
                          "IndexTurntable", "FramingGate",
                          "HemmingPress", "ClosureTurntable",
                          "RollsDynoBrakeTestBed")
            carriers = ("SkilletCarrier", "SkidConveyorModule",
                        "SkilletDeckPlate", "PFTrackSegment",
                        "OverheadTrackSegment")
            pair = (a["mesh"], b["mesh"])
            # The native robot is seven meshes composed at one
            # transform, standing at a machine station: its joints
            # overlap each other and the machine it serves by design.
            if any("BodyShopRobotNative" in m for m in pair):
                continue
            if any(any(st in m for st in straddlers) for m in pair)                     and any(any(c in m for c in carriers) for m in pair):
                continue
            # By-design pairs: cabinets stand under the pipe bridge's
            # open portal (the AABB includes the void), and the tractor
            # couples onto the trailer kingpin.
            design_pairs = (("PipeBridge_Module", "RectifierCabinet"),
                            ("Transporter_v001_Trailer",
                             "Transporter_v001_Tractor"),
                            # Carriers ride the deck plates; fixtures
                            # travel loaded on the return carts.
                            ("SkilletCarrier", "SkilletDeckPlate"),
                            ("EmptyReturnCart", "ClosureDoorFixture"),
                            # Boards hang across the overhead track;
                            # the cockpit module stages in the assist.
                            ("Sign_LineBoard", "OverheadTrackSegment"),
                            ("CockpitInstallAssist", "CockpitModule"))
            if any((p[0] in pair[0] and p[1] in pair[1]) or
                   (p[1] in pair[0] and p[0] in pair[1])
                   for p in design_pairs):
                continue
            volume = overlap_volume(a, b)
            # Ignore glancing contact under 0.15 cubic metres.
            if volume > 150000.0:
                overlaps.append({
                    "a": a["label"], "a_mesh": a["mesh"],
                    "b": b["label"], "b_mesh": b["mesh"],
                    "volume_m3": round(volume / 1e6, 2),
                })

height_issues = []
for entry in actors:
    base = entry["min"][2]
    low = entry["mesh"].lower()
    if base < -8.0 and "rollsdyno" not in low:
        # The rolls dyno is recessed into its pit by design.
        height_issues.append({"label": entry["label"],
                              "mesh": entry["mesh"],
                              "issue": "sunk", "base": round(base, 1)})
    elif base > 60.0 and "board" not in low \
            and "tray" not in low \
            and "festoon" not in low \
            and "track" not in low \
            and "chassishanger" not in low \
            and "doorcarrier" not in low:
        height_issues.append({"label": entry["label"],
                              "mesh": entry["mesh"],
                              "issue": "floating",
                              "base": round(base, 1)})

overlaps.sort(key=lambda row: -row["volume_m3"])
with open(OUT, "w") as handle:
    json.dump({"actors": len(actors), "overlaps": overlaps[:80],
               "height_issues": height_issues[:60]}, handle, indent=1)
unreal.log("LINE_BOSS_PLACEMENT_QA actors={} overlaps={} heights={}"
           .format(len(actors), len(overlaps), len(height_issues)))
