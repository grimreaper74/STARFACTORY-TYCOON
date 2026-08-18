"""Weld shop framing gate: the portal that clamps the body-in-white square.

A framing gate is recognised by its two lattice side frames bristling with clamp
pods, the crown bridge tying them over the line, and the skid rails running
through the middle. The clamps all point inward at body height; the hinge posts
on the upstream end say the frames swing open to release the shell.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, preview, reset)

reset()

# ---- skid path through the gate ------------------------------------------
for sy in (-0.45, 0.45):
    box("SkidRail", (4.4, 0.14, 0.10), (0, sy, 0.05), STEEL)
for tx in (-1.5, -0.5, 0.5, 1.5):
    box("SkidTie", (0.12, 1.02, 0.05), (tx, 0, 0.03), CHARCOAL, chamfer=False)

# ---- plinths the gate frames stand on -------------------------------------
for s in (-1.0, 1.0):
    box("Plinth", (3.6, 0.64, 0.14), (0, s * 1.95, 0.07), CHARCOAL)
    box("PlinthEdge", (3.6, 0.04, 0.025), (0, s * 1.62, 0.15), YELLOW,
        chamfer=False)

# ---- corner columns and the lattice frames --------------------------------
for s in (-1.0, 1.0):
    for cx in (-1.5, 1.5):
        column("Col", (cx, s * 1.95, 0.14), 2.45, GREEN, width=0.26)
    # Chords: bottom and top heavy, mid light.
    for fx in (-1.1, 0.0, 1.1):
        box("FrameFoot", (0.22, 0.24, 0.20), (fx, s * 1.95, 0.24), CHARCOAL)
    box("ChordBottom", (2.76, 0.20, 0.22), (0, s * 1.95, 0.42), GREEN)
    box("ChordMid", (2.76, 0.14, 0.16), (0, s * 1.95, 1.52), CHARCOAL)
    box("ChordTop", (3.34, 0.20, 0.24), (0, s * 1.95, 2.72), GREEN)
    # Verticals and crossed diagonals fill the panel.
    for vx in (-0.75, 0.0, 0.75):
        box("FrameVert", (0.13, 0.13, 2.1), (vx, s * 1.95, 1.45), GREEN)
    box("ChordHigh", (2.76, 0.12, 0.13), (0, s * 1.95, 2.15), CHARCOAL)
    for kx, ks in ((-1.25, 1.0), (1.25, -1.0)):
        box("FrameKnee", (0.55, 0.09, 0.11), (kx, s * 1.95, 2.45), CHARCOAL,
            rot=(0.0, ks * 0.7, 0.0))
    for dx, sign in ((-1.12, 1.0), (1.12, -1.0)):
        box("FrameDiag", (1.35, 0.09, 0.11), (dx, s * 1.95, 0.95), CHARCOAL,
            rot=(0.0, sign * 0.62, 0.0))

# ---- clamp pods on the inner faces ----------------------------------------
# Alternating heights so the pods hit sill and cantrail datums, all reaching
# inward toward the body. Cylinder pokes out the back of the frame; swing arm
# carries an elbow drop down to a charcoal tip pad.
for s in (-1.0, 1.0):
    for px, pz in ((-1.12, 1.0), (-0.4, 1.85), (0.4, 1.0), (1.12, 1.85),
                   (-0.75, 1.45), (0.75, 1.45)):
        box("PodMount", (0.24, 0.20, 0.34), (px, s * 1.83, pz), CHARCOAL)
        cyl("PodCyl", 0.05, 0.30, (px, s * 2.06, pz + 0.10), CHARCOAL, axis="Y")
        cyl("PodRod", 0.02, 0.20, (px, s * 1.88, pz + 0.10), STEEL, axis="Y")
        cyl("PodPivot", 0.05, 0.14, (px, s * 1.72, pz + 0.16), STEEL, axis="X")
        box("PodArm", (0.09, 0.46, 0.11), (px, s * 1.55, pz + 0.16), STEEL)
        box("PodElbow", (0.09, 0.10, 0.30), (px, s * 1.34, pz + 0.03), STEEL)
        box("PodTip", (0.12, 0.08, 0.06), (px, s * 1.34, pz - 0.13), CHARCOAL)

# ---- air manifold along each frame with drops to the pods ------------------
for s in (-1.0, 1.0):
    cyl("AirMain", 0.028, 2.7, (0, s * 2.09, 0.62), STEEL, axis="X")
    # Each drop runs from the manifold up to its own pod's cylinder height, so
    # the pipework visibly serves the clamps instead of stopping mid-air.
    for px, pz in ((-1.12, 1.0), (-0.4, 1.85), (0.4, 1.0), (1.12, 1.85),
                   (-0.75, 1.45), (0.75, 1.45)):
        cyl("AirDrop", 0.012, pz - 0.52, (px, s * 2.09, (pz + 0.72) * 0.5),
            STEEL, verts=10)
        cyl("AirElbow", 0.012, 0.14, (px, s * 2.02, pz + 0.10), STEEL,
            axis="Y", verts=10)

# ---- hinge posts on the upstream end --------------------------------------
for s in (-1.0, 1.0):
    cyl("HingePost", 0.075, 2.5, (-1.85, s * 1.95, 1.39), STEEL)
    for hz in (0.5, 1.4, 2.3):
        cyl("HingeCollar", 0.105, 0.10, (-1.85, s * 1.95, hz), CHARCOAL)
    for hz in (0.5, 2.3):
        box("HingeArm", (0.35, 0.12, 0.14), (-1.68, s * 1.95, hz), CHARCOAL)

# ---- crown bridge over the line -------------------------------------------
for bx in (-0.85, 0.85):
    box("CrownBeam", (0.42, 4.5, 0.30), (bx, 0, 2.98), GREEN)
    for s in (-1.0, 1.0):
        box("CrownGusset", (0.30, 0.12, 0.25), (bx, s * 1.9, 2.78), CHARCOAL)
box("CrownSpine", (2.2, 0.30, 0.20), (0, 0, 3.02), CHARCOAL)
box("CrownTray", (0.16, 4.2, 0.08), (0, 0, 3.17), CHARCOAL, chamfer=False)
for ty in (-1.6, 0.0, 1.6):
    box("TrayStub", (0.10, 0.10, 0.10), (0, ty, 3.10), CHARCOAL, chamfer=False)
cyl("BeaconPost", 0.02, 0.35, (0.85, 0, 3.30), STEEL)
cyl("BeaconLamp", 0.05, 0.12, (0.85, 0, 3.50), RED)

# ---- control cabinet beside the +Y frame ----------------------------------
box("CabBase", (0.55, 0.40, 0.12), (2.1, 2.45, 0.06), CHARCOAL)
box("Cabinet", (0.50, 0.36, 1.35), (2.1, 2.45, 0.80), GREEN)
box("CabDoor", (0.02, 0.32, 1.20), (1.84, 2.45, 0.82), CHARCOAL, chamfer=False)
box("CabHMI", (0.02, 0.22, 0.16), (1.83, 2.45, 1.25), WARMWHITE, chamfer=False)
cyl("CabEStop", 0.05, 0.05, (1.83, 2.35, 1.0), RED, axis="X")
cyl("CabIsolator", 0.03, 0.05, (1.83, 2.55, 1.0), YELLOW, axis="X")
cyl("CabConduit", 0.025, 0.55, (2.1, 2.45, 1.75), STEEL)

export("SM_LB_Weld_FramingGate_v001", "WeldShop/FramingGate_v001")
preview("SM_LB_Weld_FramingGate_v001", "WeldShop/FramingGate_v001")
