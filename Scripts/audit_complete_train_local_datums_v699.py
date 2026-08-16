"""Read-only local datum and installed envelope audit for complete A-D maps."""
from pathlib import Path
import json
import unreal
ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/"Saved/Audits/PressTrains/complete_train_local_datums_v699.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
maps={"A":"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694",
      **{x:f"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrain{x}_CompleteVariant_v696" for x in "BCD"}}
if OUT.exists(): raise RuntimeError("Refusing to overwrite v699")
rows={}
for letter,path in maps.items():
    if not levels.load_level(path): raise RuntimeError(path)
    actors=api.get_all_level_actors(); scope=f"LB.PressTrain.Installed.TRAIN_{letter}"
    members=[a for a in actors if scope in {str(t) for t in a.tags}]
    auth=[a for a in members if isinstance(a,unreal.LBPressTrainAStation)]
    lo=[float("inf")]*3; hi=[float("-inf")]*3
    for a in members:
        o,e=a.get_actor_bounds(False,False)
        for i,(v,d) in enumerate(zip(o.to_tuple(),e.to_tuple())): lo[i]=min(lo[i],v-d);hi[i]=max(hi[i],v+d)
    rows[letter]={"map":path,"member_count":len(members),"authority_count":len(auth),
                  "authority_location_cm":list(auth[0].get_actor_location().to_tuple()),
                  "authority_rotation_deg":list(auth[0].get_actor_rotation().to_tuple()),
                  "min_cm":lo,"max_cm":hi,"centre_cm":[(a+b)/2 for a,b in zip(lo,hi)],"size_cm":[b-a for a,b in zip(lo,hi)]}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v699","status":"PASS__READ_ONLY_LOCAL_DATUMS","trains":rows},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_LOCAL_DATUMS_V699_PASS");unreal.SystemLibrary.quit_editor()
