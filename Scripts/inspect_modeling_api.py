"""Inventory callable Unreal 5.8 geometry/modeling APIs without opening the editor."""

from pathlib import Path
import json
import unreal

names = sorted(name for name in dir(unreal) if "GeometryScript" in name or "DynamicMesh" in name or "Modeling" in name)
records = {}
for name in names:
    obj = getattr(unreal, name)
    records[name] = sorted(item for item in dir(obj) if not item.startswith("_") and any(
        token in item.lower() for token in ("mesh", "normal", "bevel", "simpl", "repair", "compact", "collision", "uv")
    ))

output = Path(unreal.Paths.project_saved_dir()) / "Audits/modeling_api_inventory.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_MODELING_API_INVENTORY_PASS classes={len(records)} path={output}")
