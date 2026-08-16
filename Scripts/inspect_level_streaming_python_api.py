"""Read-only API probe for assembling the control-room CCTV streamed stage."""

import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
names = ["EditorLevelUtils", "LevelStreamingAlwaysLoaded", "LevelStreamingDynamic", "LevelStreaming"]
payload = {}
for name in names:
    value = getattr(unreal, name, None)
    payload[name] = {
        "available": value is not None,
        "members": sorted(member for member in dir(value) if not member.startswith("__")) if value else [],
    }
payload["signatures"] = {
    "add_level_to_world": str(unreal.EditorLevelUtils.add_level_to_world.__doc__),
    "add_level_to_world_with_transform": str(unreal.EditorLevelUtils.add_level_to_world_with_transform.__doc__),
}
out = root / "Saved/Audits/ControlRoom/level_streaming_python_api_probe.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
