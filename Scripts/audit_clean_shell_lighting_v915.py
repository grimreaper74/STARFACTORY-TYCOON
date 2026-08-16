import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/clean_shell_lighting_v915.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    if isinstance(actor, (unreal.RectLight, unreal.DirectionalLight, unreal.SkyLight)):
        component = actor.get_component_by_class(unreal.LightComponentBase)
        rows.append({
            "name": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "location": list(actor.get_actor_location().to_tuple()),
            "rotation": list(actor.get_actor_rotation().to_tuple()),
            "intensity": component.get_editor_property("intensity") if component else None,
            "visible": component.get_editor_property("visible") if component else None,
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_CLEAN_SHELL_LIGHT_AUDIT_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
