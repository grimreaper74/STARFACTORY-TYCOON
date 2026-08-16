"""Repair the double-applied v004 packaging-module offsets in its candidate map."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v004"
AUDIT = ROOT / "Saved/Audits/pr004_packaging_actor_transform_repair_v004.json"
PREFIX = "LB_PR004_packaging_v004_"
ASSEMBLY_LOCATION = unreal.Vector(-280.0, 120.0, 130.5)
ASSEMBLY_ROTATION = unreal.Rotator(roll=0.0, pitch=0.0, yaw=-90.0)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

packaging = [
    actor for actor in actor_subsystem.get_all_level_actors()
    if actor.get_actor_label().startswith(PREFIX)
]
if len(packaging) != 43:
    raise RuntimeError(f"Expected 43 v004 packaging actors, found {len(packaging)}")

records = []
for actor in packaging:
    before_location = actor.get_actor_location()
    before_rotation = actor.get_actor_rotation()
    actor.set_actor_location(ASSEMBLY_LOCATION, False, False)
    actor.set_actor_rotation(ASSEMBLY_ROTATION, False)
    after_location = actor.get_actor_location()
    after_rotation = actor.get_actor_rotation()
    records.append({
        "actor": actor.get_actor_label(),
        "before_location_cm": list(before_location.to_tuple()),
        "before_rotation_deg": list(before_rotation.to_tuple()),
        "after_location_cm": list(after_location.to_tuple()),
        "after_rotation_deg": list(after_rotation.to_tuple()),
    })

if not levels.save_current_level():
    raise RuntimeError("Could not save the repaired v004 candidate map")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-packaging-actor-transform-repair-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_TRANSFORM_REPAIR_PASS__FRESH_VISUAL_GATE_REQUIRED",
    "map": MAP,
    "reason": "FBX baked Blender object transforms; manifest offsets had been applied a second time",
    "actor_count": len(records),
    "shared_assembly_location_cm": list(ASSEMBLY_LOCATION.to_tuple()),
    "shared_assembly_rotation_deg": list(ASSEMBLY_ROTATION.to_tuple()),
    "records": records,
    "promotion_supported": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_V004_TRANSFORM_REPAIR_PASS actors={len(records)} audit={AUDIT}")
