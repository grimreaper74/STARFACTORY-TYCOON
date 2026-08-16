"""Read-only Unreal 5.8 navigation configuration API inspection."""

import json
from pathlib import Path
import unreal

out = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/navigation_config_ue58_api.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level("/Game/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017"):
    raise RuntimeError("Could not load retained v017 for navigation type registration")
rows = {}
classes = [getattr(unreal, name, None) for name in
           ("NavigationSystemModuleConfig", "NavigationSystemConfig")]
for cls in [value for value in classes if value is not None]:
    obj = unreal.new_object(cls)
    rows[cls.__name__] = {
        "python_attributes": sorted(name for name in dir(obj) if not name.startswith("__")),
        "path": obj.get_path_name(),
    }
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps({name: [value for value in row["python_attributes"]
                              if "nav" in value.lower() or "spawn" in value.lower()
                              or "static" in value.lower()]
                  for name, row in rows.items()}, indent=2))
