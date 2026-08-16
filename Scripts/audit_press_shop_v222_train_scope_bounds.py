"""Read-only bounds audit to identify obstructive imported train-context actors."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v222"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v222_train_scope_bounds.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

scopes = {}
for suffix in ("TRAIN_A", "TRAIN_B", "TRAIN_C", "TRAIN_D"):
    scope = f"LB.PressTrain.Installed.{suffix}"
    rows = []
    for actor in actors_api.get_all_level_actors():
        tags = [str(tag) for tag in actor.tags]
        if scope not in tags:
            continue
        origin, extent = actor.get_actor_bounds(False, False)
        rows.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "origin_cm": [origin.x, origin.y, origin.z],
            "extent_cm": [extent.x, extent.y, extent.z],
            "max_extent_cm": max(extent.x, extent.y, extent.z),
            "volume_proxy": extent.x * extent.y * extent.z,
            "tags": tags,
        })
    scopes[scope] = {
        "count": len(rows),
        "largest_by_extent": sorted(rows, key=lambda row: row["max_extent_cm"], reverse=True)[:50],
        "largest_by_volume": sorted(rows, key=lambda row: row["volume_proxy"], reverse=True)[:50],
    }

payload = {"map": MAP, "read_only": True, "scopes": scopes}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_V222_SCOPE_BOUNDS::{json.dumps(payload)}")

