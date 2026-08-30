"""Refine v002 camera readability without adding new machine blockout.

The first correctly-oriented review showed two clear issues: temporary amber
station markers were blocking the camera, and B_stylized's isolated-hall
lumens were insufficient across a 230m open bay.  This pass hides the markers,
scales the six common fixtures for covered area (per the visual standard), and
adds functional face/task lights at the actual coil, die and robot interfaces.
"""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED=PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT=PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_readability_refine_v004.json"
TAG=unreal.Name("LB.PressShop.2126.v002.ReadabilityRefine.v004")

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

if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before=digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002")
actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("Readability refine v004 already ran")

hidden_markers=[]
for actor in actors:
    if "amber station beacon" not in actor.get_actor_label():
        continue
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False,True)
    actor.tags=list(actor.tags)+[TAG,unreal.Name("LB.PressShop.HiddenTemporaryMarker")]
    hidden_markers.append(actor.get_actor_label())
if len(hidden_markers)!=5:
    raise RuntimeError("Expected five temporary station markers, hid %d"%len(hidden_markers))

# The source reference permits intensity scale with covered area. Six fixtures
# retain the same colour/exposure language, scaled 7.5x for the 230m open bay.
scaled_fixtures=[]
for actor in actors:
    label=actor.get_actor_label()
    if not label.startswith("B_stylized | 1200 lm fixture"):
        continue
    actor.light_component.set_editor_property("intensity",9000.0)
    actor.light_component.set_editor_property("intensity_units",unreal.LightUnits.LUMENS)
    actor.tags=list(actor.tags)+[TAG,unreal.Name("LB.Lighting.B_stylized.AreaScaled")]
    scaled_fixtures.append(label)
if len(scaled_fixtures)!=6:
    raise RuntimeError("Expected six B stylized fixtures")

added=[]
for index,(label,source,target,intensity) in enumerate((
    ("coil mandrel inspection",(-14500.0,-3200.0,850.0),(-13200.0,0.0,300.0),48000.0),
    ("draw die-face",(-5200.0,-3400.0,900.0),(-4200.0,0.0,360.0),54000.0),
    ("trim die-face",(-2800.0,-3300.0,900.0),(-2100.0,0.0,360.0),54000.0),
    ("pierce die-face",(-1000.0,-3300.0,900.0),(-200.0,0.0,360.0),54000.0),
    ("flange die-face",(1000.0,-3300.0,900.0),(1600.0,0.0,360.0),54000.0),
    ("vision outfeed face",(4200.0,-3300.0,900.0),(3500.0,0.0,360.0),48000.0),
),start=1):
    light=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.RectLight,unreal.Vector(*source),aim(unreal.Vector(*source),unreal.Vector(*target)))
    if light is None:
        raise RuntimeError("Could not create process face light")
    light.set_actor_label("2126 v002 | functional process light %02d | %s"%(index,label))
    light.set_actor_rotation(aim(unreal.Vector(*source),unreal.Vector(*target)),False)
    light.tags=[TAG,unreal.Name("LB.Lighting.FunctionalTask"),unreal.Name("LB.Visual.2126")]
    component=light.light_component
    component.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE)
    component.set_editor_property("intensity",intensity)
    component.set_editor_property("intensity_units",unreal.LightUnits.LUMENS)
    component.set_editor_property("source_width",540.0)
    component.set_editor_property("source_height",260.0)
    component.set_editor_property("use_temperature",True)
    component.set_editor_property("temperature",5000.0)
    added.append(light.get_actor_label())

# Aim cameras at broad groups, never past the outermost press. The cream route
# and rear elevation stay inside each frame, leaving the sky/void out.
camera_targets={
    "CAM v002 | steam hero press run":((-9300.0,-6100.0,500.0),(-1000.0,0.0,300.0),62.0),
    "CAM v002 | coil-to-press story":((-17700.0,-3900.0,430.0),(-13000.0,0.0,300.0),68.0),
    "CAM v002 | draw plus robot":((-7700.0,-4100.0,450.0),(-4200.0,-100.0,330.0),70.0),
    "CAM v002 | press automation":((-3000.0,-4600.0,470.0),(-200.0,-100.0,320.0),70.0),
}
by_label={actor.get_actor_label():actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
for label,(source,target,focal) in camera_targets.items():
    camera=by_label.get(label)
    if camera is None:
        raise RuntimeError("Camera missing: "+label)
    camera.set_actor_location(unreal.Vector(*source),False,False)
    camera.set_actor_rotation(aim(unreal.Vector(*source),unreal.Vector(*target)),False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length",focal)
    camera.tags=list(camera.tags)+[TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v002 readability pass")
after=digest(PROTECTED)
if before!=after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({
    "status":"PASS__TEMPORARY_MARKERS_REMOVED__MESHY_READABILITY_LIGHTING_ADDED",
    "candidate_map":MAP,
    "hidden_temporary_markers":hidden_markers,
    "b_stylized_area_scale":{"fixture_count":len(scaled_fixtures),"base_lm":1200,"scaled_lm":9000,"reason":"open-bay area coverage"},
    "functional_task_lights":added,
    "roof_created":False,
    "protected_v438_sha256_before":before,
    "protected_v438_sha256_after":after,
},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_READABILITY_REFINE_V004_PASS")
