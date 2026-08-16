"""Create camera-only v142 from the technically passing but visually rejected hook v141."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

BASE="/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141"
MAP="/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142"
ROOT=Path(unreal.Paths.project_dir())
PARENT=ROOT/"Content/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141.umap"
OUT=ROOT/"Saved/Audits/press_shop_pr004_powered_chook_visual_proof_build_v142.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library=unreal.EditorAssetLibrary

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
before=sha(PARENT)
if library.does_asset_exist(MAP): raise RuntimeError(f"Refusing overwrite {MAP}")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError(MAP)

def camera(label,location,target,fov):
    actor=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*location),unreal.Rotator())
    actor.set_actor_label("LB_PR004_V142_CAM_"+label)
    actor.tags=[unreal.Name(v) for v in ("LB.Camera.Validation","LB.Camera.Fixed.PoweredCHook.v142","LB.Asset.Candidate.v142","LB.Asset.CandidateNotPromoted","LB.VisualProof.SuccessorOfRejected.v141")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(),unreal.Vector(*target)),False)
    actor.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True,"post_process_blend_weight":1.0})
    pp=actor.camera_component.get_editor_property("post_process_settings")
    pp.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":-0.10})
    actor.camera_component.set_editor_property("post_process_settings",pp)
    return actor

cameras=[
    camera("PoweredCHookSideSupport",(-6500,-1550,820),(-5050,-1550,700),34.0),
    camera("PoweredCHookBoreAxis",(-5050,-650,760),(-5050,-1550,750),38.0),
    camera("PoweredCHookUnderside",(-6250,-850,590),(-5050,-1550,650),38.0)]
if not levels.save_current_level(): raise RuntimeError("save failed")
after=sha(PARENT)
if before!=after: raise RuntimeError("v141 parent changed")
payload={"$schema":"cairnwell/audit/press-shop-pr004-powered-chook-visual-proof-build-v142/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__CAMERA_ONLY_VISUAL_PROOF_SUCCESSOR_BUILT__VISUAL_GATE_REQUIRED__NOT_PROMOTED","source_map":BASE,"map":MAP,"geometry_changed":False,"materials_changed":False,"runtime_authority_changed":False,"v141_visual_status":"REJECT__HOVER_BESIDE_READ_AND_OCCLUDED_BORE_CAMERA","fixed_cameras":[c.get_actor_label() for c in cameras],"protected_parent_sha256_before":before,"protected_parent_sha256_after":after,"promotion_authorized":False}
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
