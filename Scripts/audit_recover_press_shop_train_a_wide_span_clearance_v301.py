"""Read-only recovery audit for saved v301 after its report-writer typo."""

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300.umap"
MAP="/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301.umap"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_train_a_wide_span_clearance_build_v301_r2.json"
BASE_SHA="93BF6B46BAD2292019E31C08EF31AF9C9C21CE98BAB9A045CF7670AF5A7AA52C"
Y_ROWS=[-5250,-3750,-2250,-750,750,2250]
REMOVED=[f"LB_PRESS_Column_6000_{y}" for y in Y_ROWS]

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as s:
        for chunk in iter(lambda:s.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest().upper()

if OUT.exists(): raise RuntimeError("refusing to overwrite v301 recovery audit")
if sha(BASE_FILE)!=BASE_SHA: raise RuntimeError("v300 hash drift")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
actors=api.get_all_level_actors(); by_label={a.get_actor_label():a for a in actors}
girders=[a for a in actors if a.get_actor_label().startswith("LB_V301_WIDESPAN_TRANSFER_GIRDER_")]
cameras=[a for a in actors if a.get_actor_label().startswith("LB_V301_CAM_")]
train_counts={key:sum(1 for a in actors if f"LB.PressTrain.Installed.TRAIN_{key}" in {str(t) for t in a.tags}) for key in "ABCD"}
girder_rows=[]
for a in girders:
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    girder_rows.append({"label":a.get_actor_label(),"location_cm":[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],"scale":[a.get_actor_scale3d().x,a.get_actor_scale3d().y,a.get_actor_scale3d().z],"collision_profile":str(c.get_collision_profile_name()),"affects_navigation":bool(c.get_editor_property("can_ever_affect_navigation")),"tags":[str(t) for t in a.tags]})
failures=[]
present_removed=[label for label in REMOVED if label in by_label]
if present_removed: failures.append(f"target columns remain {present_removed}")
if len(girders)!=6: failures.append(f"girder count {len(girders)}")
if any(row["collision_profile"]!="NoCollision" or row["affects_navigation"] for row in girder_rows): failures.append("girder physical policy changed")
if train_counts!={"A":338,"B":338,"C":338,"D":338}: failures.append(f"train counts {train_counts}")
if len(cameras)!=3: failures.append(f"camera count {len(cameras)}")
payload={"$schema":"cairnwell/audit/press-shop-train-a-wide-span-clearance-build-v301-r2/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__RECOVERED_READ_ONLY_PROOF__SIX_OPERATOR_SIDE_COLUMNS_ABSENT__SIX_TBC_VISUAL_GIRDERS_PRESENT__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V301_NOT_A_PARENT","base":"/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300","map":MAP,"base_sha256":BASE_SHA,"map_sha256":sha(MAP_FILE),"source_audit":"Saved/Audits/PressShopIntegration/press_shop_structural_column_inventory_v300.json","builder_note":"Original builder saved the exact map, then hit a report-only Python false/False typo. First recovery audit falsely expected 337 actors on B-D; r2 uses the proven 338-per-train contract. Both earlier reports remain harness evidence. This fresh process audits the saved package without mutation.","removed_column_labels":REMOVED,"remaining_removed_column_labels":present_removed,"added_visual_girders":girder_rows,"span_tbc_cm":4000.0,"structural_certification":"TBC_NOT_ENGINEERING_AUTHORITY","press_train_actor_counts":train_counts,"evidence_cameras":[a.get_actor_label() for a in cameras],"promotion_authorized":False,"failures":failures}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
if failures: raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
