"""Inventory exact current PR006-PR008 actor labels and native component names."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_current_binding_labels_v273.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())
families = {}
for station_name, actor_class in (
        ("PR006", unreal.LBPR006Station), ("PR007", unreal.LBPR007Station), ("PR008", unreal.LBPR008Station)):
    stations = [actor for actor in actors if isinstance(actor, actor_class)]
    families[station_name] = {
        "station_labels": [actor.get_actor_label() for actor in stations],
        "component_names": sorted({component.get_name() for actor in stations for component in actor.get_components_by_class(unreal.SceneComponent)}),
        "presentation_labels": sorted(actor.get_actor_label() for actor in actors if station_name in actor.get_actor_label().upper()),
    }
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "families": families}, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
