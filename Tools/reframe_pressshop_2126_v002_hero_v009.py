"""Tighten the v002 hero camera around actual Meshy presses and robot."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED=PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT=PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_hero_reframe_v009.json"
TAG=unreal.Name("LB.PressShop.2126.v002.HeroReframe.v009")

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()
def aim(source,target):
    dx,dy,dz=target.x-source.x,target.y-source.y,target.z-source.z
    flat=math.sqrt(dx*dx+dy*dy)
    return unreal.Rotator(roll=0.0,pitch=math.degrees(math.atan2(dz,flat)),yaw=math.degrees(math.atan2(dy,dx)))

if not PROTECTED.is_file(): raise RuntimeError("Protected v438 missing")
before=digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP): raise RuntimeError("Could not load v002")
actors={a.get_actor_label():a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in a.tags for a in actors.values()): raise RuntimeError("v009 already applied")
camera=actors.get("CAM v002 | steam hero press run")
if camera is None: raise RuntimeError("Hero camera missing")
source=unreal.Vector(-6900.0,-3700.0,360.0)
target=unreal.Vector(-900.0,-20.0,355.0)
camera.set_actor_location(source,False,False)
camera.set_actor_rotation(aim(source,target),False)
camera.get_cine_camera_component().set_editor_property("current_focal_length",82.0)
camera.tags=list(camera.tags)+[TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source,camera.get_actor_rotation())
if not unreal.EditorLevelLibrary.save_current_level(): raise RuntimeError("Could not save v009")
after=digest(PROTECTED)
if before!=after: raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({"status":"PASS__HERO_REFRAMED_TO_MESHY_PRESS_AND_ROBOT","candidate_map":MAP,"source_cm":[source.x,source.y,source.z],"target_cm":[target.x,target.y,target.z],"focal_length_mm":82.0,"protected_v438_sha256_before":before,"protected_v438_sha256_after":after},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_HERO_REFRAME_V009_PASS")
