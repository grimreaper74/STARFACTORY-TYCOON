"""Read-only transform and attachment audit for the v014 Train A unload robot."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
TARGET_VERSION = os.environ.get("LB_PTA_ROBOT_AUDIT_TARGET_VERSION", "v014")
SOURCE_VERSION = os.environ.get("LB_PTA_ROBOT_AUDIT_SOURCE_VERSION", "v009")
MAP = os.environ.get("LB_PTA_ROBOT_AUDIT_MAP", "/Game/LineBoss/Maps/LB_PressTrainARobotVisibilityCandidate_v014")
MANIFEST_PATH = ROOT / f"SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_{SOURCE_VERSION}/PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_{SOURCE_VERSION}.json"
OUT = ROOT / f"Saved/Audits/PressTrains/press_train_a_robot_hierarchy_static_{TARGET_VERSION}.json"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
expected = {
    row["name"]: row
    for row in manifest["instances"]
    if row.get("role", "").startswith("unload_robot_")
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
failures = []
for actor in actors_api.get_all_level_actors():
    actor_tags = {str(value) for value in actor.tags}
    roles = sorted(value.removeprefix("LB.PressTrain.Role.") for value in actor_tags
                   if value.startswith("LB.PressTrain.Role.unload_robot_"))
    if not roles:
        continue
    label = actor.get_actor_label()
    source_label = label.removesuffix(f"_UE{TARGET_VERSION}")
    source = expected.get(source_label)
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    component = actor.root_component
    relative_location = component.get_editor_property("relative_location")
    relative_rotation = component.get_editor_property("relative_rotation")
    parent = actor.get_attach_parent_actor()
    origin, extent = actor.get_actor_bounds(False, False)
    world_mm = [location.x * 10.0, location.y * 10.0, location.z * 10.0]
    delta_mm = None
    if source:
        delta_mm = [world_mm[i] - source["location_mm"][i] for i in range(3)]
        if max(abs(value) for value in delta_mm) > 0.2:
            failures.append(f"{label} world-location delta {delta_mm}")
        actual_parent = parent.get_actor_label().removesuffix(f"_UE{TARGET_VERSION}") if parent else None
        if actual_parent != source.get("runtime_parent"):
            failures.append(f"{label} parent {actual_parent!r}, expected {source.get('runtime_parent')!r}")
    else:
        failures.append(f"No source-manifest record for {label}")
    rows.append({
        "actor": label,
        "source_actor": source_label,
        "roles": roles,
        "parent": parent.get_actor_label() if parent else None,
        "expected_parent": source.get("runtime_parent") if source else None,
        "world_location_mm": [round(value, 4) for value in world_mm],
        "expected_world_location_mm": source.get("location_mm") if source else None,
        "world_location_delta_mm": [round(value, 4) for value in delta_mm] if delta_mm else None,
        "world_rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
        "expected_world_rotation_deg": source.get("rotation_deg") if source else None,
        "relative_location_cm": [relative_location.x, relative_location.y, relative_location.z],
        "relative_rotation_deg": [relative_rotation.roll, relative_rotation.pitch, relative_rotation.yaw],
        "mobility": str(component.get_editor_property("mobility")),
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
    })

if len(rows) != 9:
    failures.append(f"Expected 9 unload robot actors, found {len(rows)}")

report = {
    "$schema": f"cairnwell/audit/press-train-a-robot-hierarchy-static-{TARGET_VERSION}/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": f"PASS__{TARGET_VERSION.upper()}_ROBOT_WORLD_TRANSFORMS_AND_HIERARCHY_MATCH_{SOURCE_VERSION.upper()}_SOURCE" if not failures
              else f"FAIL__{TARGET_VERSION.upper()}_ROBOT_TRANSFORM_OR_HIERARCHY_MISMATCH",
    "map": MAP,
    "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
    "actor_count": len(rows),
    "failures": failures,
    "actors": sorted(rows, key=lambda row: row["actor"]),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
