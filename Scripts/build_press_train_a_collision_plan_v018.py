"""Derive deterministic v018 collision boxes from the authored v012 Blender meshes."""

import hashlib
import json
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
source = root / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v012"
blend = source / "CA_MW_PressTrainA_AssemblyStudy_v012.blend"
manifest_path = source / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v012.json"
validation_path = source / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v012.json"
out = root / "Saved/Audits/PressTrains/press_train_a_collision_plan_v018.json"

BLOCK_UNION = {
    "planning_envelope_foundation", "operator_side_enclosure", "endpoint_operator_enclosure",
    "stage_hmi_pedestal", "fixed_press_bolster", "fixed_lower_die", "common_transfer_rail",
    "blank_feed_guard", "die_change_cart", "outfeed_stillage", "formed_panel_stillage_output",
    "blank_feed_pallet", "unload_robot_base_runtime", "runtime_hmi_mount",
}
BLOCK_COMPONENTS = {
    "heavy_press_frame", "yellow_access_guard", "inspection_arch",
    "inspection_cantilever_brace",
}
QUERY_UNION = {
    "moving_press_slide", "moving_upper_die", "carried_workpiece_state",
    "transfer_crossbar", "transfer_gripper", "destack_lift", "destack_head",
    "visible_formed_panel", "formed_panel_positive_y_discharge", "staged_formed_panel",
    "unload_robot_shoulder_runtime", "unload_robot_upper_arm_runtime",
    "unload_robot_elbow_runtime", "unload_robot_forearm_runtime",
    "unload_robot_wrist_runtime", "unload_robot_gripper_runtime", "unload_robot_tool_runtime",
}
NAV_RELEVANT = BLOCK_UNION | BLOCK_COMPONENTS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
validation = json.loads(validation_path.read_text(encoding="utf-8"))
if not validation["status"].startswith("PASS__V012_CAIRNWELL_FAMILY_PRESS_HANDLING_ROBOT_SOURCE"):
    raise RuntimeError("v012 source validation mismatch")
before = {path.name: sha(path) for path in (blend, manifest_path, validation_path)}
bpy.ops.wm.open_mainfile(filepath=str(blend))
collection = bpy.data.collections["TRAIN_A_ASSEMBLY"]
objects = {obj.name: obj for obj in collection.all_objects if obj.type == "MESH"}


def union_box(obj):
    coords = [vertex.co for vertex in obj.data.vertices]
    minimum = [min(value[i] for value in coords) for i in range(3)]
    maximum = [max(value[i] for value in coords) for i in range(3)]
    return minimum, maximum


def connected_boxes(obj):
    vertex_polygons = defaultdict(list)
    for index, polygon in enumerate(obj.data.polygons):
        for vertex in polygon.vertices:
            vertex_polygons[vertex].append(index)
    visited = set()
    groups = []
    for first in range(len(obj.data.polygons)):
        if first in visited:
            continue
        queue = deque([first]); visited.add(first); vertices = set()
        while queue:
            polygon_index = queue.popleft()
            polygon = obj.data.polygons[polygon_index]
            vertices.update(polygon.vertices)
            for vertex in polygon.vertices:
                for adjacent in vertex_polygons[vertex]:
                    if adjacent not in visited:
                        visited.add(adjacent); queue.append(adjacent)
        coords = [obj.data.vertices[index].co for index in vertices]
        minimum = [min(value[i] for value in coords) for i in range(3)]
        maximum = [max(value[i] for value in coords) for i in range(3)]
        dimensions = [maximum[i] - minimum[i] for i in range(3)]
        volume = dimensions[0] * dimensions[1] * dimensions[2]
        ordered = sorted(dimensions, reverse=True)
        if volume >= 0.0005 or (ordered[0] >= 0.30 and ordered[1] >= 0.025):
            groups.append((minimum, maximum))
    return groups


def spec(minimum, maximum, preflip_y):
    center = [(minimum[i] + maximum[i]) * 50.0 for i in range(3)]
    dimensions = [(maximum[i] - minimum[i]) * 100.0 for i in range(3)]
    if preflip_y:
        center[1] *= -1.0
    return {"center_cm": [round(value, 4) for value in center],
            "dimensions_cm": [round(max(value, 0.2), 4) for value in dimensions],
            "rotation_degrees": [0.0, 0.0, 0.0]}


rows = []
counts = defaultdict(int)
for record in manifest["instances"]:
    actor_role = record.get("role")
    if actor_role in BLOCK_UNION:
        policy = "BLOCK_ALL"; boxes = [union_box(objects[record["name"]])]
    elif actor_role in BLOCK_COMPONENTS:
        policy = "BLOCK_ALL"; boxes = connected_boxes(objects[record["name"]])
    elif actor_role in QUERY_UNION:
        policy = "QUERY_ONLY"; boxes = [union_box(objects[record["name"]])]
    else:
        continue
    if not boxes or len(boxes) > 64:
        raise RuntimeError(f"Invalid collision component count {len(boxes)} for {record['name']}")
    preflip_y = actor_role.startswith("unload_robot_")
    rows.append({
        "object": record["name"], "role": actor_role, "policy": policy,
        "nav_relevant": actor_role in NAV_RELEVANT,
        "runtime_parent": record.get("runtime_parent"),
        "boxes": [spec(minimum, maximum, preflip_y) for minimum, maximum in boxes],
    })
    counts[policy] += 1

after = {path.name: sha(path) for path in (blend, manifest_path, validation_path)}
failures = []
if before != after:
    failures.append("v012 source changed while deriving collision")
if not any(row["role"] == "planning_envelope_foundation" for row in rows):
    failures.append("foundation collision plan missing")
if len([row for row in rows if row["role"].startswith("unload_robot_")]) != 9:
    failures.append("expected collision policy for all nine robot actors")
payload = {
    "$schema": "cairnwell/source-plan/press-train-a-collision-v018/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V018_AUTHORED_GEOMETRY_COLLISION_PLAN__UNREAL_INTEGRATION_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__V018_COLLISION_PLAN__NOT_PROMOTED",
    "source_hashes_before": before, "source_hashes_after": after,
    "operator_capsule": {"radius_cm": 34.0, "half_height_cm": 88.0,
                         "authority": "Source/LineBossCarFactory/LBControlRoomPawn.cpp"},
    "navigation_agent": {"radius_cm": 35.0, "authority": "Config/DefaultEngine.ini"},
    "planned_actor_count": len(rows), "policy_actor_counts": dict(sorted(counts.items())),
    "planned_box_total": sum(len(row["boxes"]) for row in rows),
    "actors": rows,
    "policy": {
        "BLOCK_ALL": "Fixed substantial equipment and guarding physically block the standing player; foundation supports walking and navigation.",
        "QUERY_ONLY": "Moving process and robot geometry supplies sensing/sweep envelopes without becoming an unsafe physics obstacle.",
        "UNLISTED": "Fasteners, labels, cables, lights and other cosmetic/detail actors remain NoCollision."
    },
    "unverified_engineering_clearance_adopted": False,
    "failures": failures, "promotion_authorized": False,
}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "actors": len(rows),
                  "boxes": payload["planned_box_total"], "policies": payload["policy_actor_counts"]}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
