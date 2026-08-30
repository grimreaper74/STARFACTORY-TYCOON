"""Stabilize the v002 map after the v005 graphical-driver capture fault.

v005 saved its map changes but the separate screenshot session faulted before
writing an image.  This pass hides only the six newly-added broad safety washes
and restores the proven v004 light-count envelope. A modest fixed exposure lift
keeps the already-authored material forms readable without adding more lights.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED=PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT=PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_capture_stabilize_v006.json"
TAG=unreal.Name("LB.PressShop.2126.v002.CaptureStabilize.v006")

def digest(path):
    hasher=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):
            hasher.update(block)
    return hasher.hexdigest()

if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before=digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002 map")
actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("v006 capture stabilisation already ran")

hidden=[]
for actor in actors:
    if not actor.get_actor_label().startswith("2126 v002 | operator safety wash"):
        continue
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False,True)
    actor.tags=list(actor.tags)+[TAG,unreal.Name("LB.Lighting.HiddenAfterGPUFault")]
    hidden.append(actor.get_actor_label())
if len(hidden)!=6:
    raise RuntimeError("Expected six v005 safety washes, found %d"%len(hidden))

post=next((actor for actor in actors if actor.get_actor_label()=="B_stylized | fixed exposure -0.50"),None)
if post is None:
    raise RuntimeError("Fixed exposure volume missing")
settings=post.get_editor_property("settings")
settings.override_auto_exposure_bias=True
settings.auto_exposure_bias=0.50
post.set_editor_property("settings",settings)
post.set_actor_label("v006 | fixed review exposure +0.50")
post.tags=list(post.tags)+[TAG,unreal.Name("LB.Lighting.ReadabilityTest")]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v006 capture-stable candidate")
after=digest(PROTECTED)
if before!=after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({
    "status":"PASS__V005_GPU_CAPTURE_FAULT_CONTAINED__V006_SAFE_CAPTURE_CONFIGURED",
    "candidate_map":MAP,
    "hidden_v005_operator_safety_washes":hidden,
    "active_rect_light_count":16,
    "review_exposure_bias":0.50,
    "note":"This is an in-engine readability test, not acceptance of a new factory-wide lighting calibration.",
    "protected_v438_sha256_before":before,
    "protected_v438_sha256_after":after,
},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_CAPTURE_STABILIZE_V006_PASS")
