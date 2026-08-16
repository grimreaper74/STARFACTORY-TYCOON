"""Read-only Train A world envelope and station datum probe in retained v301."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_v301_world_bounds_probe_v039.json"
if OUT.exists(): raise RuntimeError("refusing to overwrite v039 probe")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
actors = api.get_all_level_actors()
scope = [a for a in actors if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
rows=[]
for actor in scope:
    origin, extent = actor.get_actor_bounds(False, False)
    rows.append({"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"location_cm":[actor.get_actor_location().x,actor.get_actor_location().y,actor.get_actor_location().z],"bounds_origin_cm":[origin.x,origin.y,origin.z],"bounds_extent_cm":[extent.x,extent.y,extent.z],"tags":[str(t) for t in actor.tags]})
valid=[r for r in rows if any(v>0 for v in r["bounds_extent_cm"])]
lo=[min(r["bounds_origin_cm"][i]-r["bounds_extent_cm"][i] for r in valid) for i in range(3)]
hi=[max(r["bounds_origin_cm"][i]+r["bounds_extent_cm"][i] for r in valid) for i in range(3)]
stations=[]
for r in rows:
    station_tags=[tag for tag in r["tags"] if "Station" in tag or "Stage" in tag]
    if station_tags or "STAGE" in r["label"].upper() or "STATION" in r["label"].upper(): stations.append(r)
payload={"map":MAP,"actor_count":len(scope),"world_bounds_cm":{"min":lo,"max":hi,"centre":[(lo[i]+hi[i])/2 for i in range(3)],"size":[hi[i]-lo[i] for i in range(3)]},"station_candidates":stations,"actors":rows}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps({"actor_count":len(scope),"world_bounds_cm":payload["world_bounds_cm"],"station_candidate_count":len(stations)},indent=2));unreal.SystemLibrary.quit_editor()
