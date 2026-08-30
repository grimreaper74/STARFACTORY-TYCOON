"""Apply named Unreal Rotator fields to correct the v002 visual orientation.

Unreal's Python Rotator positional constructor is roll, pitch, yaw. Earlier
candidate scripts passed pitch, yaw, roll positionally. This candidate-local
repair uses named fields throughout and proves the final actor rotations.
"""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED=PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT=PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_orientation_repair_v003.json"
TAG=unreal.Name("LB.PressShop.2126.v002.OrientationRepair.v003")

def digest(path):
    hasher=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):
            hasher.update(block)
    return hasher.hexdigest()

def rot(pitch=0.0,yaw=0.0,roll=0.0):
    return unreal.Rotator(roll=roll,pitch=pitch,yaw=yaw)

def aim(source,target):
    dx,dy,dz=target.x-source.x,target.y-source.y,target.z-source.z
    flat=math.sqrt(dx*dx+dy*dy)
    return rot(pitch=math.degrees(math.atan2(dz,flat)),yaw=math.degrees(math.atan2(dy,dx)))

def require(actors,label):
    if label not in actors:
        raise RuntimeError("Missing v002 actor: "+label)
    return actors[label]

if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before=digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002")
actors={actor.get_actor_label():actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("orientation repair v003 already ran")

changed=[]
for label,yaw in (
    ("S00 | wrapped master coil | project reuse",90.0),
    ("S00 | bare master coil | project reuse",90.0),
    ("MESHY v002 | S02 Draw / form",0.0),
    ("MESHY v002 | S03 Trim",90.0),
    ("MESHY v002 | S04 Pierce",0.0),
    ("MESHY v002 | S05 Flange / hem",90.0),
    ("MESHY v002 | S06 Vision / outfeed",90.0),
    ("ROBOT v002 | S01 laser-tend robot",-155.0),
    ("ROBOT v002 | S02 draw quality robot",180.0),
    ("ROBOT v002 | S04 pierce handling robot",180.0),
    ("ROBOT v002 | S06 vision stack robot",-20.0),
):
    actor=require(actors,label)
    actor.set_actor_rotation(rot(yaw=yaw),False)
    actor.tags=list(actor.tags)+[TAG]
    changed.append(label)

for index in range(1,7):
    light=require(actors,"B_stylized | 1200 lm fixture %02d"%index)
    light.set_actor_rotation(rot(pitch=-90.0),False)
    light.tags=list(light.tags)+[TAG]
    changed.append(light.get_actor_label())
sun=require(actors,"B_stylized | sun 0.30")
sun.set_actor_rotation(rot(pitch=-38.0,yaw=-28.0),False)
sun.tags=list(sun.tags)+[TAG]
changed.append(sun.get_actor_label())

for label,source,target in (
    ("2126 v002 | S00 coil change task light",(-13700.0,-1500.0,700.0),(-13200.0,0.0,260.0)),
    ("2126 v002 | S02 die quality task light",(-4800.0,-1500.0,700.0),(-4200.0,0.0,300.0)),
    ("2126 v002 | S04 pierce robot task light",(-800.0,-1500.0,700.0),(-200.0,0.0,300.0)),
    ("2126 v002 | S06 vision robot task light",(4000.0,-1600.0,700.0),(3500.0,0.0,300.0)),
):
    light=require(actors,label)
    light.set_actor_location(unreal.Vector(*source),False,False)
    light.set_actor_rotation(aim(unreal.Vector(*source),unreal.Vector(*target)),False)
    light.tags=list(light.tags)+[TAG]
    changed.append(label)

camera_targets={
    "CAM v002 | steam hero press run":((-8500.0,-5300.0,610.0),(-550.0,0.0,370.0)),
    "CAM v002 | coil-to-press story":((-17800.0,-3300.0,450.0),(-12000.0,0.0,360.0)),
    "CAM v002 | draw plus robot":((-7800.0,-3600.0,480.0),(-4200.0,-150.0,330.0)),
    "CAM v002 | press automation":((-2800.0,-4100.0,500.0),(-200.0,-250.0,320.0)),
}
camera_rows=[]
for label,(source,target) in camera_targets.items():
    camera=require(actors,label)
    camera.set_actor_location(unreal.Vector(*source),False,False)
    intended=aim(unreal.Vector(*source),unreal.Vector(*target))
    camera.set_actor_rotation(intended,False)
    actual=camera.get_actor_rotation()
    if abs(actual.yaw-intended.yaw)>0.01 or abs(actual.pitch-intended.pitch)>0.01:
        raise RuntimeError("Camera orientation failed for "+label)
    camera.tags=list(camera.tags)+[TAG]
    camera_rows.append({"label":label,"pitch":actual.pitch,"yaw":actual.yaw})
    changed.append(label)

hero=require(actors,"CAM v002 | steam hero press run")
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero.get_actor_location(),hero.get_actor_rotation())
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v002 orientation repair")
after=digest(PROTECTED)
if before!=after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({
    "status":"PASS__NAMED_ROTATOR_ORIENTATION_REPAIRED",
    "candidate_map":MAP,
    "changed":changed,
    "camera_orientations":camera_rows,
    "protected_v438_sha256_before":before,
    "protected_v438_sha256_after":after,
},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_ORIENTATION_REPAIR_V003_PASS")
