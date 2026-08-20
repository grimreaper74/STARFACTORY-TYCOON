"""Inspection scan beam - the moving laser for inspection stations.

Owner, 2026-08-21: "for inspection we should have like a laser that
moves like a car wash". A thin emissive bar spanning the body width
with small emitter housings at each end; the C++ scan actor sweeps
it back and forth along the line like a car-wash gantry.
"""
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

NAME = "SM_LB_Inspect_ScanBeam_v001"
OUT = "ScanKit_v001/" + NAME

kit.reset(); kit.glass_material()
# The laser line itself - WARMWHITE binds to the emissive glow master.
kit.box("BeamLine", (0.04, 3.6, 0.03), (0.0, 0.0, 1.2), kit.WARMWHITE,
        chamfer=False)
for sy in (-1.86, 1.86):
    kit.box("EmitterHousing", (0.16, 0.14, 0.22), (0.0, sy, 1.2),
            kit.CHARCOAL)
    kit.cyl("EmitterLens", 0.03, 0.05, (0.0, sy - 0.08 if sy > 0
            else sy + 0.08, 1.2), kit.RED, axis="Y", verts=8)
    kit.box("HangerRod", (0.05, 0.05, 0.5), (0.0, sy, 1.55),
            kit.STEEL)
kit.box("CarriageBar", (0.10, 3.9, 0.08), (0.0, 0.0, 1.83), kit.STEEL)
kit.export(NAME, OUT); kit.preview(NAME, OUT, distance=4.0, height=1.6)
print("SCANBEAM COMPLETE")
