"""Remove obsolete CR01 v004 placements from the Press Shop candidate map.

The imported v004 source assets are deliberately preserved.  This only removes
the two old robot assemblies and their provisional docks from the derivative
Press Shop map so newer candidates are not visually confused with them.
"""
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_removed_obsolete_cr01_v004_v005.json"
OBSOLETE_PREFIXES = (
    "LB_CR01_WEST_",
    "LB_CR01_EAST_",
    "LB_CR01_DOCK_WEST_",
    "LB_CR01_DOCK_EAST_",
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

all_actors = actor_system.get_all_level_actors()
targets = [
    actor
    for actor in all_actors
    if actor.get_actor_label().startswith(OBSOLETE_PREFIXES)
]
labels = sorted(actor.get_actor_label() for actor in targets)

if len(targets) != 190:
    raise RuntimeError(
        f"Refusing ambiguous cleanup: expected 190 obsolete v004/dock actors, found {len(targets)}"
    )

if not actor_system.destroy_actors(targets):
    raise RuntimeError("Unreal did not confirm deletion of obsolete actors")

remaining = [
    actor.get_actor_label()
    for actor in actor_system.get_all_level_actors()
    if actor.get_actor_label().startswith(OBSOLETE_PREFIXES)
]
if remaining:
    raise RuntimeError(f"Obsolete CR01 actors remain: {remaining[:10]}")

if not levels.save_current_level():
    raise RuntimeError("Could not save cleaned Press Shop v005 map")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(
    json.dumps(
        {
            "status": "PASS",
            "map": MAP,
            "operation": "removed obsolete map placements only; source assets preserved",
            "removed_actor_count": len(labels),
            "removed_actor_labels": labels,
            "remaining_obsolete_actor_count": 0,
            "preserved_source_assets": "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v004",
        },
        indent=2,
    ),
    encoding="utf-8",
)
unreal.log(f"LINE_BOSS_REMOVE_OBSOLETE_CR01_V004_PASS actors={len(labels)} audit={AUDIT}")
