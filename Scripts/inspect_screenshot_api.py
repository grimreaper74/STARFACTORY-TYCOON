"""Print Unreal screenshot-related Python APIs for the headless evidence runner."""

import unreal

for owner_name in ("AutomationLibrary", "EditorAutomationLibrary", "SystemLibrary"):
    owner = getattr(unreal, owner_name, None)
    if owner is None:
        continue
    for attribute in sorted(name for name in dir(owner) if "screenshot" in name.lower() or "camera" in name.lower()):
        value = getattr(owner, attribute)
        unreal.log(f"LINE_BOSS_API {owner_name}.{attribute} doc={getattr(value, '__doc__', '')}")

task_type = getattr(unreal, "AutomationEditorTask", None)
if task_type is not None:
    for attribute in sorted(name for name in dir(task_type) if "task" in name.lower() or "done" in name.lower() or "complete" in name.lower()):
        value = getattr(task_type, attribute)
        unreal.log(f"LINE_BOSS_API AutomationEditorTask.{attribute} doc={getattr(value, '__doc__', '')}")
