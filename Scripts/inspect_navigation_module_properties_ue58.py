"""Probe exact reflected property spellings on UE 5.8 module config."""

import json
from pathlib import Path
import unreal

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level("/Game/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017")
cls = unreal.load_class(None, "/Script/NavigationSystem.NavigationSystemModuleConfig")
obj = unreal.new_object(cls)
names = [
    "navigation_system_class", "NavigationSystemClass",
    "strictly_static", "b_strictly_static", "bStrictlyStatic",
    "create_on_client", "b_create_on_client", "bCreateOnClient",
    "auto_spawn_missing_nav_data", "b_auto_spawn_missing_nav_data", "bAutoSpawnMissingNavData",
    "spawn_nav_data_in_nav_bounds_level", "b_spawn_nav_data_in_nav_bounds_level",
    "bSpawnNavDataInNavBoundsLevel",
]
rows = {}
for name in names:
    try:
        rows[name] = {"readable": True, "value": str(obj.get_editor_property(name))}
    except Exception as exc:
        rows[name] = {"readable": False, "error": str(exc)}
out = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/navigation_module_properties_ue58.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"class": obj.get_class().get_path_name(), "properties": rows}, indent=2), encoding="utf-8")
print(json.dumps({name: row for name, row in rows.items() if row["readable"]}, indent=2))
