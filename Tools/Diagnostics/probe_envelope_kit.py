"""Measure candidate building-shell assets before converting the runtime envelope.

The shops' walls and roofs exist only while a dev console command runs. Rebuilding
them as saved content from 200 cm concrete panels would take roughly 1,500 actors per
shop to reach 22 m, so establish what larger units exist first. Measured, not assumed -
guessing sizes is what produced a mezzanine that read as painted floor.
"""
import io
import json
import os

import unreal

OUT = os.environ.get("LB_ENVKIT_OUT", "C:/Temp/lb_envkit.json")
CANDIDATES = [
    "/Game/Meshes/SM_ConcreteWall",
    "/Game/Meshes/SM_FrontWall01",
    "/Game/Meshes/SM_ConcretePillar01",
    "/Game/Meshes/SM_ConcretePillar02",
    "/Game/Meshes/SM_FactoryFloorLarge01",
    "/Game/Meshes/SM_ConcreteFloor_01",
    "/Game/Meshes/SM_LargeWindowFramed",
    # A whole shed in one actor - potentially the building rather than its bricks.
    "/Game/Meshes/SM_Background2_Hangar",
    "/Game/Meshes/SM_Background2_BoxBuilding",
    "/Game/Meshes/SM_Background2_BoxBuildingFrame",
    "/Game/Meshes/SM_Background1_Frame",
    # Roof and truss candidates.
    "/Game/Meshes/SM_MetalBeam01",
    "/Game/Meshes/SM_Roof_01",
    "/Game/Meshes/SM_RoofPart_01",
    "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/"
    "SM_LB_ShutterBay_Frame_v001",
    "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/"
    "SM_LB_ShutterBay_StaticWall_v001",
    "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/"
    "SM_LB_ShutterLeaf_v001",
]

report = []
for path in CANDIDATES:
    mesh = unreal.load_asset(path)
    if mesh is None:
        report.append({"name": path.rsplit("/", 1)[-1], "missing": True})
        continue
    box = mesh.get_bounding_box()
    size = box.max - box.min
    report.append({
        "name": path.rsplit("/", 1)[-1],
        "path": path,
        "size_cm": [round(size.x, 1), round(size.y, 1), round(size.z, 1)],
        "min_z": round(box.min.z, 1),
        "slots": len(mesh.static_materials),
    })

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1))
unreal.log("LINE_BOSS_ENVKIT measured {} of {} -> {}".format(
    sum(1 for r in report if not r.get("missing")), len(CANDIDATES), OUT))
