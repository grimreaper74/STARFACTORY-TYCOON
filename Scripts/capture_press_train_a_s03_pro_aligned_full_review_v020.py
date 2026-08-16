"""Fresh full-machine source review for immutable Pro-aligned v020."""
import bpy, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v020/CA_MW_PressModulePrototype_v020.blend"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v020/FullMachineReview"
REPORT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v020/PRESS_MODULE_FULL_MACHINE_REVIEW_v020.json"
OUT.mkdir(parents=True,exist_ok=True)
if REPORT.exists(): raise RuntimeError("refusing to overwrite v020 review")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene=bpy.context.scene
scene.render.resolution_x=1500; scene.render.resolution_y=1500; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
camera=bpy.data.objects.get("PressModule_v020_Camera")
if camera is None: raise RuntimeError("v020 camera missing")
def look(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
mat=next((m for m in bpy.data.materials if "FabricatedGraphite" in m.name),None)
bpy.ops.mesh.primitive_plane_add(size=34,location=(0,0,-.02)); floor=bpy.context.object; floor.data.materials.append(mat)
views=[
 ("01_full_operator_v020.png",(15,-19,9),(0,0,4.65),67),
 ("02_full_front_v020.png",(0,-23,4.7),(0,0,4.7),72),
 ("03_full_left_v020.png",(-19,0,5.2),(0,0,4.6),70),
 ("04_full_rear_v020.png",(0,23,4.9),(0,0,4.7),72)]
for name,loc,target,lens in views:
    camera.location=loc; camera.data.lens=lens; look(camera,target); scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)
REPORT.write_text(json.dumps({"status":"FRESH_FULL_MACHINE_PRO_REFERENCE_COMPARISON_REQUIRED__NOT_PROMOTED","source":str(SOURCE.relative_to(ROOT)).replace("\\","/"),"source_changed":False,"renders":[str((OUT/v[0]).relative_to(ROOT)).replace("\\","/") for v in views],"promotion_authorized":False},indent=2),encoding="utf-8")
print(REPORT)
