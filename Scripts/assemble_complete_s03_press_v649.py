"""Assemble a source-only complete S03 visual validation press.

Uses the retained v643 8.2 m core and accepted/repaired v647-v648 modules.
All dimensions remain explicit visual/TBC until the isolated Unreal scale gate.
"""
import bpy
import json
import math
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / r"SourceAssets\Candidate\PressTrains\TrainA\Meshy6CorrectedCoreAssembly_v643\CA_MW_PressTrainA_Meshy6CorrectedCoreAssembly_v643.blend"
BASE = ROOT / r"SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Generated\Meshy6_v646"
REPAIRED = BASE / "Repaired_v648"
OUT = ROOT / r"SourceAssets\Candidate\PressTrains\TrainA\CompleteS03Assembly_v649"
REVIEW = OUT / "Review"
OUT.mkdir(parents=True, exist_ok=True)
REVIEW.mkdir(parents=True, exist_ok=True)
BLEND = OUT / "CA_MW_PTA_S03_CompleteVisualAssembly_v649.blend"
MANIFEST = OUT / "ASSEMBLY_MANIFEST_v649.json"
if BLEND.exists() or MANIFEST.exists():
    raise RuntimeError("Refusing to overwrite v649")

ASSETS = {
 "RamSlide": BASE / r"01_RamSlide\Cleaned_v647\SM_CA_MW_PT_01_RamSlide_LOD0_v639.glb",
 "UpperDie": BASE / r"02_UpperDie\Cleaned_v647\SM_CA_MW_PT_02_UpperDie_LOD0_v639.glb",
 "LowerDie": BASE / r"03_LowerDie\Cleaned_v647\SM_CA_MW_PT_03_LowerDie_LOD0_v639.glb",
 "LeftDoor": BASE / r"04_LeftAccessDoor\Cleaned_v647\SM_CA_MW_PT_04_LeftAccessDoor_LOD0_v639.glb",
 "RightDoor": REPAIRED / "SM_CA_MW_PT_RightAccessDoor_LOD0_v648.glb",
 "Fence": REPAIRED / "SM_CA_MW_PT_FixedSafetyFence_LOD0_v648.glb",
 "Gate": REPAIRED / "SM_CA_MW_PT_InterlockedGate_LOD0_v648.glb",
 "Cabinet": BASE / r"08_ElectricalCabinet\Cleaned_v647\SM_CA_MW_PT_08_ElectricalCabinet_LOD0_v639.glb",
 "HMI": BASE / r"09_OperatorHMI\Cleaned_v647\SM_CA_MW_PT_09_OperatorHMI_LOD0_v639.glb",
 "Housing": BASE / r"10_FlywheelHousing\Cleaned_v647\SM_CA_MW_PT_10_FlywheelHousing_LOD0_v639.glb",
 "Rotor": BASE / r"11_FlywheelRotorShaft\Cleaned_v647\SM_CA_MW_PT_11_FlywheelRotorShaft_LOD0_v639.glb",
}

def bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo, hi

def import_one(key, target_size, location, rot_z=0.0, floor=False):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(ASSETS[key]))
    meshes = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = "SM_CA_MW_PTA_S03_" + key + "_v649"
    lo, hi = bounds(obj)
    size = hi - lo
    obj.scale = tuple(target_size[i] / max(size[i], 1e-6) for i in range(3))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    lo, hi = bounds(obj)
    obj.location -= (lo + hi) * 0.5
    obj.rotation_euler[2] = math.radians(rot_z)
    obj.location += Vector(location)
    bpy.context.view_layer.update()
    if floor:
        lo, _ = bounds(obj)
        obj.location.z -= lo.z
    obj["lineboss_scale_status"] = "VISUAL_TBC_PENDING_UNREAL_GATE"
    obj["lineboss_runtime_authority"] = "NONE_SOURCE_ONLY"
    obj["lineboss_collision_status"] = "NOT_AUTHORED"
    return obj

def look(camera, target):
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
# Keep S03 core and floor/reference only; remove other press cores and P0 train modules
# so this review cannot conceal a placement error behind repeated machinery.
for obj in list(bpy.data.objects):
    if obj.type == "MESH" and obj.name != "SM_CA_MW_PTA_S03_StaticPressShell_v643":
        bpy.data.objects.remove(obj, do_unlink=True)

station_y = 15.0
placed = []
# Local Meshy X is component width and is rotated into train-world Y for front-facing modules.
placed.append(import_one("LowerDie", (3.4,2.4,0.65), (0.0,station_y,1.45), 90))
placed.append(import_one("UpperDie", (3.4,2.2,0.75), (0.0,station_y,2.45), 90))
placed.append(import_one("RamSlide", (3.5,2.0,1.35), (0.0,station_y,3.65), 90))
placed.append(import_one("LeftDoor", (1.30,0.18,2.65), (-2.55,station_y-1.35,3.65), 90))
placed.append(import_one("RightDoor", (1.30,0.18,2.65), (-2.55,station_y+1.35,3.65), 90))
placed.append(import_one("Housing", (2.15,0.65,2.35), (0.10,station_y+2.55,5.35), 0))
placed.append(import_one("Rotor", (1.65,0.42,1.65), (-0.30,station_y+2.92,5.35), 0))
placed.append(import_one("Cabinet", (1.75,1.05,2.30), (-4.25,station_y+2.55,0), 90, True))
placed.append(import_one("HMI", (0.85,0.70,1.70), (-4.30,station_y-2.15,0), 90, True))
placed.append(import_one("Fence", (1.90,0.16,1.83), (-3.65,station_y+1.85,0), 90, True))
placed.append(import_one("Gate", (1.62,0.30,1.90), (-3.65,station_y-0.10,0), 90, True))

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for obj in list(bpy.data.objects):
    if obj.type == "CAMERA": bpy.data.objects.remove(obj, do_unlink=True)

views = (
 ("operator_three_quarter", (-16.0,8.0,8.0), (0,station_y,3.6), 13.5),
 ("operator_front", (-18.0,station_y,4.2), (0,station_y,4.0), 11.5),
 ("flywheel_side", (-7.0,25.0,7.0), (0,station_y,4.0), 12.5),
 ("floor_gate", (-11.0,10.5,2.2), (-2.5,station_y,1.8), 10.5),
)
renders=[]
for name, loc, target, ortho in views:
    bpy.ops.object.camera_add(location=loc)
    cam=bpy.context.object; cam.data.type="ORTHO"; cam.data.ortho_scale=ortho
    look(cam,target); scene.camera=cam
    path=REVIEW/f"S03_{name}_v649.png"; scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True); renders.append(str(path))
    bpy.data.objects.remove(cam,do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
manifest={
 "revision":"v649", "status":"COMPLETE_S03_VISUAL_SOURCE_NOT_PROMOTED",
 "generated_utc":datetime.now(timezone.utc).isoformat(), "station":"S03", "station_y_m":station_y,
 "shell_height_m_visual_tbc":8.2, "parts":[o.name for o in placed], "sources":{k:str(v) for k,v in ASSETS.items()},
 "renders":renders, "collision":"pending", "navigation":"pending", "gameplay":"pending",
 "protected_map_modified":False, "promotion_authorized":False,
}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("LB_S03_V649="+json.dumps(manifest,separators=(",",":")))
