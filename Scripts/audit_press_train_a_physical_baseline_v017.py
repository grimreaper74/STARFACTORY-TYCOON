"""Read-only physical-gameplay baseline for retained Train A v017."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
map_path = "/Game/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017"
map_file = root / "Content/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017.umap"
out = root / "Saved/Audits/PressTrains/press_train_a_physical_baseline_v017.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def tags(actor):
    return {str(value) for value in actor.tags}


def role(actor):
    values = sorted(value.removeprefix("LB.PressTrain.Role.") for value in tags(actor)
                    if value.startswith("LB.PressTrain.Role."))
    return values[0] if values else None


def primitive_counts(mesh):
    if not mesh:
        return {"box": 0, "sphere": 0, "capsule": 0, "convex": 0, "total": 0}
    body = mesh.get_editor_property("body_setup")
    if not body:
        return {"box": 0, "sphere": 0, "capsule": 0, "convex": 0, "total": 0}
    agg = body.get_editor_property("agg_geom")
    row = {
        "box": len(agg.get_editor_property("box_elems")),
        "sphere": len(agg.get_editor_property("sphere_elems")),
        "capsule": len(agg.get_editor_property("sphyl_elems")),
        "convex": len(agg.get_editor_property("convex_elems")),
    }
    row["total"] = sum(row.values())
    return row


rows = []
by_role = defaultdict(list)
all_actors = actors_api.get_all_level_actors()
for actor in all_actors:
    actor_role = role(actor)
    if not actor_role or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    origin, extent = actor.get_actor_bounds(False, False)
    collision_enabled = str(component.get_editor_property("body_instance").get_editor_property("collision_enabled"))
    row = {
        "actor": actor.get_actor_label(), "role": actor_role,
        "mesh": mesh.get_path_name() if mesh else None,
        "collision_enabled": collision_enabled,
        "collision_profile": str(component.get_collision_profile_name()),
        "world_static_response": str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC)),
        "pawn_response": str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)),
        "can_ever_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        "simple_collision": primitive_counts(mesh),
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
    }
    rows.append(row)
    by_role[actor_role].append(row)

summary = {}
for name, role_rows in sorted(by_role.items()):
    summary[name] = {
        "actor_count": len(role_rows),
        "collision_enabled_count": sum("NO_COLLISION" not in row["collision_enabled"].upper() for row in role_rows),
        "pawn_block_count": sum("BLOCK" in row["pawn_response"].upper() for row in role_rows),
        "nav_relevant_count": sum(row["can_ever_affect_navigation"] for row in role_rows),
        "simple_primitive_total": sum(row["simple_collision"]["total"] for row in role_rows),
    }

robot_rows = [row for row in rows if row["role"].startswith("unload_robot_")]
robot_min = [min(row["bounds_origin_cm"][i] - row["bounds_extent_cm"][i] for row in robot_rows) for i in range(3)]
robot_max = [max(row["bounds_origin_cm"][i] + row["bounds_extent_cm"][i] for row in robot_rows) for i in range(3)]
nearby = []
for row in rows:
    if row in robot_rows or row["role"] in {"positive_y_flow_marker", "positive_y_panel_discharge",
                                            "visible_formed_panel", "carried_workpiece_state"}:
        continue
    minimum = [row["bounds_origin_cm"][i] - row["bounds_extent_cm"][i] for i in range(3)]
    maximum = [row["bounds_origin_cm"][i] + row["bounds_extent_cm"][i] for i in range(3)]
    horizontal_gap = ((max(0.0, robot_min[0] - maximum[0], minimum[0] - robot_max[0]) ** 2
                       + max(0.0, robot_min[1] - maximum[1], minimum[1] - robot_max[1]) ** 2) ** 0.5)
    if horizontal_gap <= 600.0:
        nearby.append({"actor": row["actor"], "role": row["role"],
                       "horizontal_aabb_gap_cm": horizontal_gap,
                       "bounds_min_cm": minimum, "bounds_max_cm": maximum})
nearby.sort(key=lambda row: row["horizontal_aabb_gap_cm"])

nav_bounds = [actor.get_actor_label() for actor in all_actors if isinstance(actor, unreal.NavMeshBoundsVolume)]
player_starts = [actor.get_actor_label() for actor in all_actors if isinstance(actor, unreal.PlayerStart)]
blocking = [row for row in rows if "BLOCK" in row["pawn_response"].upper()
            and "NO_COLLISION" not in row["collision_enabled"].upper()
            and row["simple_collision"]["total"] > 0]
foundation = summary.get("planning_envelope_foundation", {})
failures = []
if len(rows) != 336:
    failures.append(f"expected 336 presentation actors, found {len(rows)}")
if blocking:
    failures.append(f"baseline unexpectedly has {len(blocking)} physically blocking presentation actors")
if foundation.get("simple_primitive_total", 0) != 0:
    failures.append("baseline foundation unexpectedly has simple collision")

report = {
    "$schema": "cairnwell/audit/press-train-a-physical-baseline-v017/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V017_PHYSICAL_BASELINE_CONFIRMS_RELEASE_COLLISION_AND_NAVIGATION_ARE_OPEN__READ_ONLY__NOT_PROMOTED"
              if not failures else "FAIL__V017_PHYSICAL_BASELINE_INCONSISTENT__NOT_PROMOTED",
    "map": map_path, "map_sha256": sha(map_file),
    "presentation_actor_count": len(rows),
    "blocking_presentation_actor_count": len(blocking),
    "nav_mesh_bounds_volume_count": len(nav_bounds), "nav_mesh_bounds_volumes": nav_bounds,
    "player_start_count": len(player_starts), "player_starts": player_starts,
    "operator_capsule_authority": {"source": "LBControlRoomPawn.cpp", "radius_cm": 34.0, "half_height_cm": 88.0},
    "navigation_agent_authority": {"source": "Config/DefaultEngine.ini", "radius_cm": 35.0},
    "presentation_actors": rows,
    "role_collision_summary": summary,
    "robot_rest_bounds_cm": {"min": robot_min, "max": robot_max},
    "nearest_non_robot_actor_bounds": nearby[:25],
    "assessment": "The retained visual map has presentation collision disabled and no simple primitives; it cannot yet prove standing-player floor support, equipment blocking, navigable approach or robot service clearance.",
    "failures": failures, "production_map_changed": False, "promotion_authorized": False,
}
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "blocking": len(blocking),
                  "nav_bounds": len(nav_bounds), "player_starts": len(player_starts)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
