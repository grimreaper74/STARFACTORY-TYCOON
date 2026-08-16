"""Fresh bright matched review of source-only Train A v031; no source mutation."""
import bpy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v031/CA_MW_PressTrainA_ModularAssembly_v031.blend";OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v031/MatchedReview";REPORT=OUT/"PRESS_TRAIN_A_MATCHED_REVIEW_v031.json"
OUT.mkdir(parents=True,exist_ok=True)
if REPORT.exists() or any(OUT.glob("*.png")):raise RuntimeError("refusing to overwrite v031 matched review")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest().upper()
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene
for o in list(bpy.data.objects):
 if o.type in {"LIGHT","CAMERA"}:bpy.data.objects.remove(o,do_unlink=True)
world=scene.world or bpy.data.worlds.new("MatchedReviewWorld_v031");scene.world=world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.10,.12,.14,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
scene.view_settings.look="AgX - Medium High Contrast";scene.view_settings.exposure=1.35
for loc,e,size in (((45,-5,28),15000,22),((-42,50,24),13000,22),((0,22,38),12000,28),((30,25,10),8000,16)):bpy.ops.object.light_add(type="AREA",location=loc);l=bpy.context.object;l.data.energy=e;l.data.size=size
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type="ORTHO";scene.camera=cam;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.render.film_transparent=False
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
views=(("operator",(72,22.5,5.7),(0,22.5,4.4),52),("rear",(-72,22.5,5.7),(0,22.5,4.4),52),("elevated",(55,-18,34),(0,22.5,3.3),60),("top",(0,22.5,90),(0,22.5,0),52))
captures=[]
for name,loc,target,scale in views:
 cam.location=loc;cam.data.ortho_scale=scale;look(cam,target)
 if name=="top":cam.rotation_euler.z=0
 path=OUT/f"train_a_matched_{name}_v031.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);captures.append({"view":name,"file":path.name,"sha256":sha(path)})
payload={"$schema":"cairnwell/source/press-train-a-matched-review-v031/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_BRIGHT_MATCHED_SOURCE_REVIEW__HUMAN_DECISION_REQUIRED__NOT_PROMOTED","source_sha256":sha(SRC),"captures":captures,"source_mutated":False,"promotion_authorized":False};REPORT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
