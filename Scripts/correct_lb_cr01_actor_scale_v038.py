"""Apply absolute actor-root scaling for CR01 v038 after UE Interchange ignores FBX import scale."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_ModularRig_v038"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_cr01_actor_scale_v038.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
corrected = []
for actor in actors_api.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_CR01_V038_SM_"):
        continue
    root = actor.get_editor_property("root_component")
    root.set_absolute(False, False, True)
    actor.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
    corrected.append(actor.get_actor_label())
if len(corrected) != 16:
    raise RuntimeError(f"Expected 16 modular actors, corrected {len(corrected)}")
if not levels.save_current_level():
    raise RuntimeError("Could not save corrected CR01 v038 map")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "ABSOLUTE_ACTOR_SCALE_PASS__VISUAL_GATE_PENDING",
    "actor_count": len(corrected), "absolute_scale": 100.0,
    "reason": "UE 5.8 Interchange reimport ignored import_uniform_scale",
    "actors": sorted(corrected),
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_LB_CR01_V038_ACTOR_SCALE_PASS")
