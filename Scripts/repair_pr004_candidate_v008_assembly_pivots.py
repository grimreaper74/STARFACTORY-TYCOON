"""Repair PR-004 v008 inherited multipart assemblies using v007 authored transforms."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"
SOURCE_AUDIT = PROJECT / "Saved/Audits/pr004_v007_actor_transforms.json"
OUT = PROJECT / "Saved/Audits/pr004_v008_assembly_pivot_repair.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def set_transform(actor, location, rotation):
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(unreal.Rotator(rotation[0], rotation[1], rotation[2]), False)


try:
    if not SOURCE_AUDIT.exists():
        raise RuntimeError(f"Missing source transform audit {SOURCE_AUDIT}")
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")

    source_rows = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))["actors"]
    source = {row["label"]: row for row in source_rows}
    current = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    repaired = []
    removed = []

    # Bare-coil baseline: one coherent coil on the powered V-cradle. Remove
    # obsolete packaging-state meshes instead of leaving them off-cell.
    bare_label = "LB_PR004_packaging_v004_PR004-PACK-BARE-COIL-v004"
    for label, actor in list(current.items()):
        if label.startswith("LB_PR004_packaging_v004_") and label != bare_label:
            actors.destroy_actor(actor)
            removed.append(label)

    for label, row in source.items():
        if label == bare_label or label.startswith("LB_PR004_powered_cradle_v001_"):
            actor = current.get(label)
            if actor is None:
                raise RuntimeError(f"Missing cradle assembly actor {label}")
            loc = row["location_cm"]
            set_transform(actor, (loc[0] - 400.0, loc[1] - 120.0, loc[2]), row["rotation_deg"])
            repaired.append(label)

    # Restore the coherent authored robot pose at the new cell-centre datum.
    rack_prefixes = (
        "LB_PR004_robot_v002_tool_rack",
        "LB_PR004_robot_v002_band_",
        "LB_PR004_robot_v002_wrap_",
        "LB_PR004_robot_v002_edge_",
        "LB_PR004_robot_v002_inspection_",
    )
    for label, row in source.items():
        if not label.startswith("LB_PR004_robot_v002_") or label.startswith(rack_prefixes):
            continue
        actor = current.get(label)
        if actor is None:
            continue
        loc = row["location_cm"]
        set_transform(actor, (loc[0] + 40.0, loc[1] - 70.0, loc[2]), row["rotation_deg"])
        repaired.append(label)

    # Reconstruct each rack tool as a rigid assembly from its v007 local
    # offsets, then place all four docks across the north/rear rack.
    tool_roots = {
        "band": ("LB_PR004_robot_v002_band_tool", (-135.0, 437.0, 108.0)),
        "wrap": ("LB_PR004_robot_v002_wrap_tool", (-45.0, 437.0, 108.0)),
        "edge": ("LB_PR004_robot_v002_edge_tool", (45.0, 437.0, 108.0)),
        "inspection": ("LB_PR004_robot_v002_inspection_tool", (135.0, 437.0, 108.0)),
    }
    rack = current.get("LB_PR004_robot_v002_tool_rack")
    if rack is None:
        raise RuntimeError("Missing tool rack")
    set_transform(rack, (0.0, 470.0, 0.0), source["LB_PR004_robot_v002_tool_rack"]["rotation_deg"])
    repaired.append(rack.get_actor_label())

    for key, (root_label, target) in tool_roots.items():
        source_root = source[root_label]["location_cm"]
        for label, row in source.items():
            if not label.startswith(f"LB_PR004_robot_v002_{key}_"):
                continue
            actor = current.get(label)
            if actor is None:
                continue
            loc = row["location_cm"]
            offset = (loc[0] - source_root[0], loc[1] - source_root[1], loc[2] - source_root[2])
            set_transform(actor, (target[0] + offset[0], target[1] + offset[1], target[2] + offset[2]), row["rotation_deg"])
            repaired.append(label)

    if not levels.save_current_level():
        raise RuntimeError("Failed to save repaired PR-004 v008 map")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-v008-assembly-pivot-repair/v1",
        "map": MAP,
        "status": "ASSEMBLY_TRANSFORM_REPAIR_PASS__VISUAL_REVIEW_REQUIRED",
        "repaired_count": len(set(repaired)),
        "removed_obsolete_packaging_count": len(removed),
        "repaired": sorted(set(repaired)),
        "removed": sorted(removed),
        "promotion_supported": False,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V008_PIVOT_REPAIR_PASS repaired={len(set(repaired))} removed={len(removed)} audit={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
