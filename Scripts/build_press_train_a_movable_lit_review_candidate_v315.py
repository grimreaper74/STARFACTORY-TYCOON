"""Create an upright Train A studio using runtime-evaluated movable review lights."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressTrainA_AxisCorrectedStudioCandidate_v309"
MAP = "/Game/LineBoss/Maps/LB_PressTrainA_MovableLitReviewCandidate_v315"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainA_AxisCorrectedStudioCandidate_v309.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainA_MovableLitReviewCandidate_v315.umap"
BASE_SHA = "EDABB0950A6D9D94C00E40F88E1BD4D6A7E63C94FD6A992ED1830A2480E25542"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_movable_lit_review_build_v315.json"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
if sha(BASE_FILE) != BASE_SHA: raise RuntimeError("v309 hash drift")
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v315")
if not levels.new_level_from_template(MAP, BASE): raise RuntimeError("fresh v309 child failed")
candidate = next((a for a in api.get_all_level_actors() if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}), None)
if candidate is None: raise RuntimeError("candidate missing")
origin, extent = candidate.get_actor_bounds(False)
added = []
for i, x in enumerate((origin.x-2200, origin.x-750, origin.x+750, origin.x+2200), 1):
    for side, y in (("front", origin.y-950), ("rear", origin.y+950)):
        light = api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, origin.z+620), unreal.Rotator())
        light.set_actor_label(f"LB_V315_MOVABLE_{side.upper()}_{i:02d}")
        comp = light.point_light_component
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_editor_properties({"intensity":85000.0,"attenuation_radius":3000.0,"source_radius":160.0,"soft_source_radius":320.0,"cast_shadows":False,"light_color":unreal.Color(242,247,255,255)})
        added.append(light.get_actor_label())
sun = api.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(origin.x,origin.y,origin.z+1600), unreal.Rotator(-35,-25,0))
sun.set_actor_label("LB_V315_MOVABLE_DIRECTIONAL")
sun.directional_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
sun.directional_light_component.set_editor_properties({"intensity":2.5,"cast_shadows":False,"light_color":unreal.Color(255,248,235,255)})
added.append(sun.get_actor_label())
fail=[]
if len(added)!=9: fail.append(f"review light count {len(added)}")
if not levels.save_current_level(): fail.append("save failed")
if sha(BASE_FILE)!=BASE_SHA: fail.append("v309 changed")
payload={"$schema":"cairnwell/audit/press-train-a-movable-lit-review-v315/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__MOVABLE_LIGHT_REVIEW_READY__NOT_PROMOTED" if not fail else "FAIL__V315_NOT_EVIDENCE","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"movable_review_lights":added,"geometry_changed":False,"runtime_authority_changed":False,"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail: raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
