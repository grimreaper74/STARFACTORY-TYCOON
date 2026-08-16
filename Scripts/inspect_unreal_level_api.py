"""Log the UE 5.8 level-editor Python methods used by build tooling."""

import unreal


level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for name in sorted(item for item in dir(level) if "level" in item.lower() or "save" in item.lower()):
    unreal.log(f"LB_LEVEL_API {name}")

for name in sorted(item for item in dir(unreal.EditorLevelLibrary) if "level" in item.lower() or "save" in item.lower()):
    unreal.log(f"LB_EDITOR_LEVEL_LIBRARY_API {name}")
