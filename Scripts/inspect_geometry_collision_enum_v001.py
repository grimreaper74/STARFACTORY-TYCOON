"""Record UE 5.8 Geometry Script collision enum values without changing assets."""

import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
output = root / "Saved/Audits/geometry_collision_enum_v001.json"


def public_names(value):
    return sorted(name for name in dir(value) if not name.startswith("_"))


enum_type = unreal.GeometryScriptCollisionGenerationMethod
payload = {
    "engine_version": str(unreal.SystemLibrary.get_engine_version()),
    "enum_type": str(enum_type),
    "public_names": public_names(enum_type),
    "iterated_values": [str(value) for value in enum_type],
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_GEOMETRY_COLLISION_ENUM_V001_PASS audit={output}")
unreal.SystemLibrary.quit_editor()
