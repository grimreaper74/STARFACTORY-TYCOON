"""Assembly overhead chassis track: one 4 m goalpost segment of the carrier line.

The carrier change at station 9 is the spine of the GA shop: the body rides an
ELEVATED track through marriage and underbody. One segment is recognised by
its goalpost columns, the running rail under the bridge, the festoon cable
loops, and the drip tray. Floor pivot; the rail runs along local X at 3.9 m so
segments chain end to end.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()

# Goalpost: two kit columns and a bridge beam.
for sy in (-1.35, 1.35):
    column("Post", (0, sy, 0.0), 4.0, GREEN, width=0.30)
box("Bridge", (0.55, 3.1, 0.34), (0, 0, 4.35), GREEN)
for sy in (-1.28, 1.28):
    box("BridgeGusset", (0.40, 0.14, 0.30), (0, sy, 4.00), CHARCOAL)

# I-beam running rail hanging under the bridge on visible hanger plates.
box("RailTopFlange", (4.0, 0.22, 0.04), (0, 0, 4.06), CHARCOAL, chamfer=False)
box("RailWeb", (4.0, 0.08, 0.24), (0, 0, 3.92), CHARCOAL)
box("RailBottomFlange", (4.0, 0.26, 0.05), (0, 0, 3.78), STEEL)
for hx in (-1.5, 0.0, 1.5):
    box("HangerPlate", (0.16, 0.05, 0.14), (hx, 0, 4.13), CHARCOAL)
# Butt plates with bolt bosses at both rail ends so segments read chained.
for ex in (-1.99, 1.99):
    box("ButtPlate", (0.03, 0.30, 0.34), (ex, 0, 3.92), CHARCOAL,
        chamfer=False)
    for bz in (3.80, 4.04):
        cyl("ButtBolt", 0.016, 0.05, (ex, 0.10, bz), STEEL, axis="X", verts=8)
        cyl("ButtBolt", 0.016, 0.05, (ex, -0.10, bz), STEEL, axis="X", verts=8)
# Festoon cable loops hanging under the rail - real rings, not discs.
import bpy
from lb_model_kit import material
for n in range(5):
    fx = -1.5 + n * 0.75
    bpy.ops.mesh.primitive_torus_add(
        location=(fx, 0, 3.70), rotation=(1.5708, 0.0, 0.0),
        major_radius=0.20, minor_radius=0.018,
        major_segments=24, minor_segments=8)
    loop = bpy.context.active_object
    loop.name = "FestoonLoop"
    loop.data.materials.append(material(*CHARCOAL))

export("SM_LB_Assembly_OverheadTrackSegment_v001",
       "AssemblyShop/OverheadTrack_v001")
preview("SM_LB_Assembly_OverheadTrackSegment_v001",
        "AssemblyShop/OverheadTrack_v001")
