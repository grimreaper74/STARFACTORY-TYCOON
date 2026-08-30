"""Disable v005 light components after its GPU capture fault, map-local only."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED=PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT=PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_disable_v005_lights_v007.json"
TAG=unreal.Name("LB.PressShop.2126.v002.DisableV005Lights.v007")

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before=digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002")
actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("v007 already ran")
disabled=[]
for actor in actors:
    if not actor.get_actor_label().startswith("2126 v002 | operator safety wash"):
        continue
    if not isinstance(actor,unreal.Light):
        raise RuntimeError("Expected Light actor: "+actor.get_actor_label())
    component=actor.light_component
    component.set_visibility(False,True)
    component.set_editor_property("affects_world",False)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags=list(actor.tags)+[TAG,unreal.Name("LB.Lighting.DisabledAfterGPUFault")]
    disabled.append(actor.get_actor_label())
if len(disabled)!=6:
    raise RuntimeError("Expected six disabled v005 lights, got %d"%len(disabled))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v007")
after=digest(PROTECTED)
if before!=after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({
    "status":"PASS__V005_GPU_FAULT_LIGHTS_DISABLED_AT_COMPONENT_LEVEL",
    "candidate_map":MAP,
    "disabled_lights":disabled,
    "remaining_active_dynamic_light_target":16,
    "protected_v438_sha256_before":before,
    "protected_v438_sha256_after":after,
},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_DISABLE_V005_LIGHTS_V007_PASS")
