"""Read-only class/component inventory for retained complete Train A."""
from collections import Counter
from pathlib import Path
import json, unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/PressShopIntegration/retained_train_installed_classes_v20260809_v001.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
source = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694"
if out.exists(): raise RuntimeError("Refusing overwrite")
if not levels.load_level(source): raise RuntimeError("Could not load donor")
members = [a for a in actors.get_all_level_actors() if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
classes = Counter(a.get_class().get_path_name() for a in members)
components = Counter()
rows=[]
for a in members:
    comps=[c.get_class().get_path_name() for c in a.get_components_by_class(unreal.ActorComponent)]
    components.update(comps)
    rows.append({"label":a.get_actor_label(),"class":a.get_class().get_path_name(),"components":comps,"tags":[str(t) for t in a.tags]})
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"source":source,"count":len(members),"classes":dict(classes),"components":dict(components),"actors":rows},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_RETAINED_TRAIN_CLASS_INSPECTION_PASS")
unreal.SystemLibrary.quit_editor()
