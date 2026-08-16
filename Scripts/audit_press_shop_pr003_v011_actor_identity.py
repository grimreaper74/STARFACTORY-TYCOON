"""Read-only actor identity dump for the PR-003 v011 derivative."""
import json
from pathlib import Path
import unreal
MAP="/Game/LineBoss/Maps/LB_PressShop_PR003StorageCandidate_v011"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/press_shop_pr003_v011_actor_identity.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(f"Could not load {MAP}")
rows=[]
for actor in actors.get_all_level_actors():
    label=actor.get_actor_label()
    if "Coil" in label or "CS-" in label or "PR00" in label:
        rows.append({"label":label,"class":actor.get_class().get_name(),"tags":[str(x) for x in actor.tags]})
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"map":MAP,"matched":len(rows),"actors":rows},indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_PR003_V011_IDENTITY_PASS matched={len(rows)}")
unreal.SystemLibrary.quit_editor()
