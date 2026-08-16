"""Assemble retained Meshy 6 press cores and optimized P0 supporting sources."""
import bpy, json, math, hashlib
from pathlib import Path
from datetime import datetime, timezone
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CORE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/Meshy6CoreEvaluation_v636/LB_TrainA_Meshy6Core_Evaluation_v636.blend"
P0 = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/Meshy6SupportingSystemsProduction_v638"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/Meshy6P0Assembly_v640"
REVIEW = OUT / "Review"
OUT.mkdir(parents=True, exist_ok=True); REVIEW.mkdir(parents=True, exist_ok=True)
BLEND = OUT / "CA_MW_PressTrainA_Meshy6P0Assembly_v640.blend"
MANIFEST = OUT / "ASSEMBLY_MANIFEST_v640.json"
if BLEND.exists() or MANIFEST.exists():
    raise RuntimeError("Refusing to overwrite v640")

DATUMS = {"S01":0.0,"S02":7.5,"S03":15.0,"S04":22.5,"S05":30.0,"S06":37.5,"S07":45.0}
SUPPORTS = {
    "S01": P0/"01_S01DestackBlankFeed/Cleaned_v639/SM_CA_MW_PTA_S01_DestackBlankFeed_LOD0_v639.glb",
    "TRANSFER": P0/"02_InterPressTransferSystem/Cleaned_v639/SM_CA_MW_PTA_TR_InterPressTransfer_LOD0_v639.glb",
    "S04": P0/"03_S04TrimScrapSystem/Cleaned_v639/SM_CA_MW_PTA_S04_TrimScrapSystem_LOD0_v639.glb",
    "S05": P0/"04_S05SlugCollectionSystem/Cleaned_v639/SM_CA_MW_PTA_S05_SlugCollection_LOD0_v639.glb",
    "S07": P0/"05_S07InspectUnloadCell/Cleaned_v639/SM_CA_MW_PTA_S07_InspectUnload_LOD0_v639.glb",
}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest().upper()
def bounds(objects):
    pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo,hi
def look(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
def collection(name):
    c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); return c
def move_to_collection(obj,c):
    for old in list(obj.users_collection): old.objects.unlink(obj)
    c.objects.link(obj)
def import_glb(path,name,target_max,location,rotation_z=0.0,c=None):
    before=set(bpy.context.scene.objects); bpy.ops.import_scene.gltf(filepath=str(path)); new=[o for o in bpy.context.scene.objects if o not in before and o.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in new:o.select_set(True)
    bpy.context.view_layer.objects.active=new[0]
    if len(new)>1:bpy.ops.object.join()
    o=bpy.context.object; o.name=name
    lo,hi=bounds([o]); scale=target_max/max(hi-lo); o.scale=(scale,scale,scale); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    lo,hi=bounds([o]); o.location-=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z)); o.rotation_euler[2]=math.radians(rotation_z); o.location+=Vector(location)
    if c:move_to_collection(o,c)
    o["engineering_dimensions"]="TBC_VISUAL_SCALE_ONLY";o["runtime_authority"]="NONE_SOURCE_ONLY";o["collision_intent"]="PENDING_ISOLATED_GATE"
    return o

bpy.ops.wm.read_factory_settings(use_empty=True)
root=collection("CA_MW_PressTrainA_Meshy6P0_v640")
stages={s:collection(f"PTA_{s}_v640") for s in DATUMS}

with bpy.data.libraries.load(str(CORE),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith("LB_Meshy6_PressCore_S")]
for obj in dst.objects:
    if not obj:continue
    bpy.context.scene.collection.objects.link(obj)
    station=obj.name.rsplit("_",1)[-1]
    obj.location=(0,DATUMS[station],0);obj.rotation_euler[2]=0
    obj.name=f"SM_CA_MW_PTA_{station}_Meshy6PressCore_v640";move_to_collection(obj,stages[station])
    obj["runtime_authority"]="NONE_SOURCE_ONLY";obj["collision_intent"]="NoCollision_VISUAL_SOURCE"

records=[]
s01=import_glb(SUPPORTS["S01"],"SM_CA_MW_PTA_S01_DestackBlankFeed_v640",6.4,(0,DATUMS["S01"],0),90,stages["S01"]);records.append(("S01",s01,SUPPORTS["S01"]))
s04=import_glb(SUPPORTS["S04"],"SM_CA_MW_PTA_S04_TrimScrap_v640",5.1,(5.4,DATUMS["S04"],0),90,stages["S04"]);records.append(("S04",s04,SUPPORTS["S04"]))
s05=import_glb(SUPPORTS["S05"],"SM_CA_MW_PTA_S05_SlugCollection_v640",5.0,(5.3,DATUMS["S05"],0),90,stages["S05"]);records.append(("S05",s05,SUPPORTS["S05"]))
s07=import_glb(SUPPORTS["S07"],"SM_CA_MW_PTA_S07_InspectUnload_v640",6.4,(0,DATUMS["S07"],0),90,stages["S07"]);records.append(("S07",s07,SUPPORTS["S07"]))
transfer_master=import_glb(SUPPORTS["TRANSFER"],"SM_CA_MW_PTA_TR_Transfer_01_v640",5.0,(0,11.25,0),90,root);records.append(("TRANSFER_01",transfer_master,SUPPORTS["TRANSFER"]))
for i,y in enumerate((18.75,26.25,33.75),2):
    o=transfer_master.copy();o.data=transfer_master.data;root.objects.link(o);o.location.y=y;o.name=f"SM_CA_MW_PTA_TR_Transfer_{i:02d}_v640"

# Review-only floor and lighting.
bpy.ops.mesh.primitive_cube_add(location=(0,22.5,-0.12));floor=bpy.context.object;floor.name="ReviewFloor_v640";floor.dimensions=(18,57.65,.24);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
mat=bpy.data.materials.new("M_ReviewFloor_v640");mat.diffuse_color=(.22,.24,.26,1);mat.roughness=.75;floor.data.materials.append(mat)
world=bpy.data.worlds.new("ReviewWorld_v640");bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.12,.14,.16,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.55
for loc,energy,size in (((-18,-8,24),7000,14),((18,25,22),6500,14),((-8,52,20),6000,12)):
    bpy.ops.object.light_add(type="AREA",location=loc);l=bpy.context.object;l.data.energy=energy;l.data.size=size;look(l,(0,22.5,3.5))
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.view_settings.look="AgX - Medium High Contrast"
views=(("operator_elevation",(-36,22.5,7),(0,22.5,4),56),("rear_elevation",(36,22.5,7),(0,22.5,4),56),("elevated_operator",(-35,-18,28),(0,22.5,3.2),62),("top_plan",(0,22.5,82),(0,22.5,0),60))
renders=[]
for name,loc,target,ortho in views:
    bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=ortho;look(cam,target);scene.camera=cam;scene.render.filepath=str(REVIEW/f"TrainA_{name}_v640.png");bpy.ops.render.render(write_still=True);renders.append(str(scene.render.filepath));bpy.data.objects.remove(cam,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
manifest={"revision":"v640","status":"SOURCE_ONLY_P0_ASSEMBLY_NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),"datum_authority":{"station_centres_y_m":DATUMS,"source":"retained v012/v031","protected_footprint_m":57.65},"core_source":str(CORE),"support_sources":[{"role":r,"file":str(p),"sha256":sha(p)} for r,o,p in records],"transfer_instances":4,"engineering_dimensions":"TBC","runtime_authority_added":False,"collision_authored":False,"renders":renders,"protected_map_modified":False}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("LB_ASSEMBLY="+json.dumps(manifest,separators=(",",":")))
