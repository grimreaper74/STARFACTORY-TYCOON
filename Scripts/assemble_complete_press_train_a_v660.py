"""Assemble complete source-only Train A from validated modular S03 and P0/P1 systems."""
import bpy,json,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
from mathutils import Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
BASE=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\Meshy6CorrectedCoreAssembly_v643\CA_MW_PressTrainA_Meshy6CorrectedCoreAssembly_v643.blend"
S03=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteS03Assembly_v649\CA_MW_PTA_S03_CompleteVisualAssembly_v649.blend"
P1=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\Meshy6SupportingSystemsProduction_v641"
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteTrainAAssembly_v660";REVIEW=OUT/"Review"
OUT.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
BLEND=OUT/"CA_MW_PressTrainA_CompleteAssembly_v660.blend";MANIFEST=OUT/"ASSEMBLY_MANIFEST_v660.json"
if BLEND.exists() or MANIFEST.exists():raise RuntimeError("Refusing to overwrite v660")
DATUMS={f"S{i:02d}":7.5*(i-1) for i in range(2,7)}
P1_ASSETS={
 "DieCart":P1/r"01_DieChangeCart\Cleaned_v644\SM_CA_MW_PT_DieChangeCart_LOD0_v639.glb",
 "HPU":P1/r"02_HydraulicPowerUnit\Cleaned_v644\SM_CA_MW_PT_HydraulicPowerUnit_LOD0_v639.glb",
 "LargeBin":P1/r"03_LargeTrimScrapBin\Cleaned_v644\SM_CA_MW_PT_LargeTrimScrapBin_LOD0_v639.glb",
 "SmallBin":P1/r"04_SmallSlugBin\Cleaned_v644\SM_CA_MW_PT_SmallSlugBin_LOD0_v639.glb",
 "Stillage":P1/r"05_FlatPanelStillage\Cleaned_v644\SM_CA_MW_PT_FlatPanelStillage_LOD0_v639.glb",
 "Conveyor":P1/r"06_PoweredRollerConveyor\Cleaned_v644\SM_CA_MW_PT_PoweredRollerConveyor_LOD0_v639.glb"}
def bounds(objs):
 pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));return lo,hi
def cube(name,loc,scale,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:m=o.modifiers.new("EdgeSoftening","BEVEL");m.width=bevel;m.segments=2
 return o
def import_scaled(path,name,target_max,loc,rot=0):
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(path));objs=[o for o in bpy.context.scene.objects if o not in before and o.type=="MESH"]
 bpy.ops.object.select_all(action="DESELECT")
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]
 if len(objs)>1:bpy.ops.object.join()
 o=bpy.context.object;o.name=name;lo,hi=bounds([o]);s=target_max/max(hi-lo);o.scale=(s,s,s);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 lo,hi=bounds([o]);o.location-=(lo+hi)*.5;o.rotation_euler[2]=math.radians(rot);o.location+=Vector(loc);bpy.context.view_layer.update();lo,_=bounds([o]);o.location.z-=lo.z
 o["lineboss_scale_status"]="VISUAL_TBC";o["lineboss_runtime_authority"]="NONE_SOURCE_ONLY";return o
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()

bpy.ops.wm.open_mainfile(filepath=str(BASE))
# Append the validated S03 modules once, then use linked mesh data for all five stations.
with bpy.data.libraries.load(str(S03),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith("SM_CA_MW_PTA_S03_") and "StaticPressShell" not in n]
templates=[]
for o in dst.objects:
 if o is not None:bpy.context.scene.collection.objects.link(o);templates.append(o)
if len(templates)!=11:raise RuntimeError(f"Expected 11 S03 modules, got {len(templates)}")
module_instances=[]
for station,y in DATUMS.items():
 delta=y-15.0
 for template in templates:
  if station=="S03":obj=template
  else:
   obj=template.copy();obj.data=template.data;bpy.context.scene.collection.objects.link(obj)
  role=template.name.replace("SM_CA_MW_PTA_S03_","").replace("_v649","")
  obj.name=f"SM_CA_MW_PTA_{station}_{role}_v660";obj.location.y+=delta
  obj["lineboss_station"]=station;obj["lineboss_shared_geometry"]="S03_v649"
  module_instances.append(obj)

# P1 service/handling placement. Unique meshes are reused via linked instances.
die_master=import_scaled(P1_ASSETS["DieCart"],"SM_CA_MW_PTA_S02_DieCart_v660",2.6,(-6.6,DATUMS["S02"],0),90)
for station in ("S03","S04","S05","S06"):
 o=die_master.copy();o.data=die_master.data;o.name=f"SM_CA_MW_PTA_{station}_DieCart_v660";o.location.y=DATUMS[station];bpy.context.scene.collection.objects.link(o)
hpu1=import_scaled(P1_ASSETS["HPU"],"SM_CA_MW_PTA_HPU_01_v660",2.8,(6.4,15,0),90)
hpu2=hpu1.copy();hpu2.data=hpu1.data;hpu2.name="SM_CA_MW_PTA_HPU_02_v660";hpu2.location.y=30;bpy.context.scene.collection.objects.link(hpu2)
import_scaled(P1_ASSETS["LargeBin"],"SM_CA_MW_PTA_S04_LargeTrimBin_v660",2.4,(6.5,22.5,0),90)
import_scaled(P1_ASSETS["SmallBin"],"SM_CA_MW_PTA_S05_SmallSlugBin_v660",1.35,(6.2,30,0),90)
import_scaled(P1_ASSETS["Stillage"],"SM_CA_MW_PTA_S07_FlatPanelStillage_v660",3.2,(-5.2,45,0),90)
import_scaled(P1_ASSETS["Conveyor"],"SM_CA_MW_PTA_S06S07_PoweredConveyor_v660",5.2,(0,41.25,0),90)

# Zero-credit shared service platform and ladder modules at each press.
service=[]
for station,y in DATUMS.items():
 deck=cube(f"SM_CA_MW_PTA_{station}_ServicePlatform_v660",(5.35,y,3.05),(.75,2.45,.09));service.append(deck)
 for yy in (y-2.35,y+2.35):service.append(cube(f"SM_CA_MW_PTA_{station}_PlatformRailPost_v660",(6.02,yy,3.65),(.035,.035,.65),.01))
 service.append(cube(f"SM_CA_MW_PTA_{station}_PlatformRailTop_v660",(6.02,y,4.27),(.035,2.4,.035),.01))
 # Two ladder stiles and eight rungs; all stay separate source pieces for collision simplification.
 for xx in (5.75,6.15):service.append(cube(f"SM_CA_MW_PTA_{station}_LadderStile_v660",(xx,y-2.55,1.52),(.025,.025,1.52),.008))
 for z in (.25,.62,.99,1.36,1.73,2.10,2.47,2.84):service.append(cube(f"SM_CA_MW_PTA_{station}_LadderRung_v660",(5.95,y-2.55,z),(.22,.025,.025),.008))
for o in service:o["lineboss_source_status"]="ZERO_CREDIT_PROCEDURAL_SERVICE_ACCESS_TBC"

scene=bpy.context.scene;scene.render.engine="BLENDER_WORKBENCH";scene.display.shading.light="STUDIO";scene.display.shading.studio_light="paint.sl";scene.display.shading.color_type="MATERIAL";scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type="WORLD"
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
for o in list(bpy.data.objects):
 if o.type=="CAMERA":bpy.data.objects.remove(o,do_unlink=True)
views=(("operator_elevation",(-55,22.5,8),(0,22.5,3.8),60),("operator_elevated",(-48,-15,28),(0,22.5,3.3),64),("service_rear",(45,22.5,13),(0,22.5,3.8),60),("top_plan",(0,22.5,88),(0,22.5,0),62))
renders=[]
for name,loc,target,ortho in views:
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=ortho;look(cam,target);scene.camera=cam
 path=REVIEW/f"TrainA_{name}_v660.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);renders.append(str(path));bpy.data.objects.remove(cam,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
lo,hi=bounds([o for o in bpy.context.scene.objects if o.type=="MESH"])
manifest={"revision":"v660","status":"COMPLETE_TRAIN_A_VISUAL_SOURCE_NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),
 "base":str(BASE),"validated_module_source":str(S03),"station_centres_y_m":DATUMS,"press_count":5,"module_instances":len(module_instances),
 "p1_unique_sources":{k:str(v) for k,v in P1_ASSETS.items()},"die_cart_instances":5,"hpu_instances":2,
 "procedural_service_access_objects":len(service),"bounds_m":{"min":[round(v,3) for v in lo],"max":[round(v,3) for v in hi],"size":[round(v,3) for v in hi-lo]},
 "renders":renders,"meshy_credits_spent_this_revision":0,"confirmed_balance":7345,"collision":"pending whole-train proxies","navigation":"pending","runtime":"pending whole-train map",
 "protected_map_modified":False,"promotion_authorized":False}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8");print("LB_TRAIN_A_V660="+json.dumps({"status":manifest["status"],"modules":len(module_instances),"bounds":manifest["bounds_m"]["size"]},separators=(",",":")))
