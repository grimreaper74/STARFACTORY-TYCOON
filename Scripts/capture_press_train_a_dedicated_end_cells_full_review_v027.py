"""Capture complete-cell evidence for source-only S01/S07 v027."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCells_v027/CA_MW_PressTrainA_DedicatedEndCells_v027.blend"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCells_v027/FullCellReview"
REPORT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCells_v027/DEDICATED_END_CELLS_FULL_REVIEW_v027.json"
OUT.mkdir(parents=True,exist_ok=True)
if REPORT.exists() or any(OUT.glob("*.png")): raise RuntimeError("refusing to overwrite v027 full review")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene; root=bpy.data.collections.get("CA_MW_PressTrainA_DedicatedEndCells_v027")
if not root: raise RuntimeError("v027 root missing")
cells={"S01":next(c for c in root.children if c.name.startswith("S01_")),"S07":next(c for c in root.children if c.name.startswith("S07_"))}
camera=next((o for o in bpy.data.objects if o.type=="CAMERA"),None)
if not camera:
    bpy.ops.object.camera_add(); camera=bpy.context.object
scene.camera=camera; camera.data.lens=58
scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
def bounds(coll):
    pts=[o.matrix_world@Vector(c) for o in coll.objects if o.type in {"MESH","CURVE","FONT"} and not o.name.startswith("SM_CA_MW_") for c in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3))); hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo,hi
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
records=[]
for key,coll in cells.items():
    for k,c in cells.items(): c.hide_render=(k!=key)
    lo,hi=bounds(coll); centre=(lo+hi)/2; size=hi-lo; span=max(size.x,size.y,size.z)
    views=(("operator",Vector((1.15,-1.55,.72))),("front",Vector((0,-1.85,.30))),("elevated",Vector((1.30,-1.45,1.05))))
    for name,direction in views:
        camera.location=centre+direction.normalized()*span*2.15; look(camera,centre+Vector((0,0,size.z*.04)))
        fn=f"{key.lower()}_{name}_full_v027.png"; path=OUT/fn; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); records.append({"cell":key,"view":name,"file":"FullCellReview/"+fn,"sha256":sha(path)})
for c in cells.values(): c.hide_render=False
payload={"$schema":"cairnwell/source/dedicated-end-cells-full-review-v027/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_FULL_CELL_VISUAL_REVIEW_CAPTURED__HUMAN_DECISION_REQUIRED__NOT_PROMOTED","source_sha256":sha(SOURCE),"captures":records,"promotion_authorized":False}
REPORT.write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps(payload,indent=2))
