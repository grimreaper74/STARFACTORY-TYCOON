"""Record the Unreal 5.8 Python surface for deterministic viewport control."""

import json
from pathlib import Path

import unreal


out = Path(unreal.Paths.project_saved_dir()) / "Audits/unreal_viewport_python_api_v001.json"
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
clients = []
get_clients = getattr(editor, "get_level_viewport_clients", None)
if get_clients:
    for index, client in enumerate(get_clients()):
        clients.append({
            "index": index,
            "type": str(type(client)),
            "attributes": sorted(name for name in dir(client) if "view" in name.lower() or "mode" in name.lower()),
        })
payload = {
    "subsystem_type": str(type(editor)),
    "subsystem_attributes": sorted(name for name in dir(editor) if "view" in name.lower() or "mode" in name.lower()),
    "viewport_clients": clients,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_VIEWPORT_API_AUDIT={out}")
unreal.SystemLibrary.quit_editor()
