"""Replace rejected low/wide v640 press cores with the Pro-aligned v642 shell."""
import bpy, json, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/Meshy6P0Assembly_v640/CA_MW_PressTrainA_Meshy6P0Assembly_v640.blend"
CORE=ROOT/"SourceAssets/Candidate/PressTrains/Shared/MeshyStaticPressShell_v642/SM_CA_MW_PT_Shared_StaticPressShell_LOD0_v639.glb"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/Meshy6CorrectedCoreAssembly_v643";REVIEW=OUT/"Review"
OUT.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
BLEND=OUT/"CA_MW_PressTrainA_Meshy6CorrectedCoreAssembly_v643.blend";MANIFEST=OUT/"CORRECTION_MANIFEST_v643.json"
if BLEND.exists() or MANIFEST.exists():raise RuntimeError("Refusing to overwrite v643")
DATUMS={"S02":7.5,"S03":15.0,"S04":22.5,"S05":30.0,"S06":37.5}
def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest().upper()
def bounds(objects):
 pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box];lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));return lo,hi
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for o in list(bpy.data.objects):
 if o.name.startswith("SM_CA_MW_PTA_S0") and "Meshy6PressCore" in o.name:bpy.data.objects.remove(o,do_unlink=True)

before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(CORE));new=[o for o in bpy.context.scene.objects if o not in before and o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.context.view_layer.objects.active=new[0]
if len(new)>1:bpy.ops.object.join()
master=bpy.context.object;master.name='SM_CA_MW_PTA_S02_StaticPressShell_v643'
lo,hi=bounds([master]);scale=8.2/(hi.z-lo.z);master.scale=(scale,scale,scale);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
lo,hi=bounds([master]);master.location-=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));master.location.y=DATUMS['S02'];master.rotation_euler[2]=0
master['engineering_dimensions']='TBC_PRO_ALIGNED_VISUAL_SCALE';master['runtime_authority']='NONE_SOURCE_ONLY';master['collision_intent']='NoCollision_VISUAL_SOURCE'
for station,y in list(DATUMS.items())[1:]:
 o=master.copy();o.data=master.data;bpy.context.scene.collection.objects.link(o);o.location.y=y;o.name=f'SM_CA_MW_PTA_{station}_StaticPressShell_v643'

scene=bpy.context.scene;scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
views=(("operator_elevation",(-45,22.5,7),(0,22.5,4.2),58),("elevated_operator",(-40,-17,30),(0,22.5,3.8),64),("top_plan",(0,22.5,84),(0,22.5,0),61))
renders=[]
for name,loc,target,ortho in views:
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=ortho;look(cam,target);scene.camera=cam;path=REVIEW/f'TrainA_{name}_v643.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);renders.append(str(path));bpy.data.objects.remove(cam,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
manifest={'revision':'v643','status':'CORRECTED_CORE_PROPORTION_REVIEW_NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'rejected_parent':'v640 retained only as failed scale evidence','source_assembly':str(SOURCE),'replacement_core':str(CORE),'replacement_sha256':sha(CORE),'press_shell_height_m_visual_tbc':8.2,'station_centres_y_m':DATUMS,'core_instances':5,'renders':renders,'protected_map_modified':False,'promotion_authorized':False}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('LB_CORRECTION='+json.dumps(manifest,separators=(',',':')))
