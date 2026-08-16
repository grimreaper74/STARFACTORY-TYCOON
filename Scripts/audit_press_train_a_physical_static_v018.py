"""Exact static gate for isolated Train A physical-gameplay v018."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
map_path = "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v018"
map_file = root / "Content/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v018.umap"
build_path = root / "Saved/Audits/PressTrains/press_train_a_physical_gameplay_build_v018.json"
out = root / "Saved/Audits/PressTrains/press_train_a_physical_static_v018.json"
protected = {
    "v017": (root / "Content/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017.umap",
             "E647EB62C3552CF39EFFE83687C2A3AA058C0323F2DD53DACFD5FD0738B02E42"),
    "v013": (root / "Content/LineBoss/Maps/LB_PressTrainASightlineCandidate_v013.umap",
             "24DB4253EB910A1282891F38CA52D6A8B5A93E2D01E1ECE9006A57CF12A56683"),
    "v107": (root / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap",
             "E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77"),
    "v213": (root / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap",
             "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def tags(actor):
    return {str(value) for value in actor.tags}


def primitive_count(mesh):
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    return sum(len(agg.get_editor_property(name)) for name in
               ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems"))


build = json.loads(build_path.read_text(encoding="utf-8"))
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
actors = actors_api.get_all_level_actors()
presentation = [actor for actor in actors if isinstance(actor, unreal.StaticMeshActor)
                and any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))]
blocking = [actor for actor in presentation if "LB.Collision.TrainA.Blocking.v018" in tags(actor)]
query = [actor for actor in presentation if "LB.Collision.TrainA.QueryMover.v018" in tags(actor)]
unlisted = [actor for actor in presentation if actor not in blocking and actor not in query]
rows = []
failures = []
for actor, policy in [(actor, "BLOCK_ALL") for actor in blocking] + [(actor, "QUERY_ONLY") for actor in query]:
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    collision_enabled = str(component.get_editor_property("body_instance").get_editor_property("collision_enabled"))
    pawn_response = str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN))
    count = primitive_count(mesh)
    row = {"actor": actor.get_actor_label(), "policy": policy, "mesh": mesh.get_path_name(),
           "collision_enabled": collision_enabled, "profile": str(component.get_collision_profile_name()),
           "pawn_response": pawn_response,
           "nav_relevant": bool(component.get_editor_property("can_ever_affect_navigation")),
           "simple_primitive_count": count}
    if count <= 0:
        failures.append(f"selected collision actor has no primitive: {row}")
    if policy == "BLOCK_ALL" and ("QUERY_AND_PHYSICS" not in collision_enabled.upper()
                                  or "BLOCK" not in pawn_response.upper()):
        failures.append(f"blocking policy mismatch: {row}")
    if policy == "QUERY_ONLY" and ("QUERY_ONLY" not in collision_enabled.upper()
                                   or "BLOCK" in pawn_response.upper()):
        failures.append(f"query policy mismatch: {row}")
    rows.append(row)
unlisted_enabled = []
for actor in unlisted:
    component = actor.static_mesh_component
    collision_enabled = str(component.get_editor_property("body_instance").get_editor_property("collision_enabled"))
    if "NO_COLLISION" not in collision_enabled.upper():
        unlisted_enabled.append({"actor": actor.get_actor_label(), "collision_enabled": collision_enabled})
if unlisted_enabled:
    failures.append(f"unlisted visual collision enabled: {unlisted_enabled}")

starts = [actor for actor in actors if isinstance(actor, unreal.PlayerStart)
          and "LB.PlayerStart.StandingOperator" in tags(actor)]
nav_bounds = [actor for actor in actors if isinstance(actor, unreal.NavMeshBoundsVolume)]
authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
legacy_safety_volumes = []
for actor in actors:
    if "SimpleCollision" not in actor.get_actor_label():
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    legacy_safety_volumes.append({
        "actor": actor.get_actor_label(), "tags": sorted(tags(actor)),
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "collision_profile": str(component.get_collision_profile_name()) if component else None,
        "collision_enabled": (str(component.get_editor_property("body_instance").get_editor_property("collision_enabled"))
                              if component else None),
    })
if len(presentation) != 336: failures.append(f"expected 336 presentation actors, found {len(presentation)}")
if len(blocking) != 61: failures.append(f"expected 61 blocking actors, found {len(blocking)}")
if len(query) != 65: failures.append(f"expected 65 query movers, found {len(query)}")
if sum(row["simple_primitive_count"] for row in rows) != 489:
    failures.append(f"expected 489 simple primitives, found {sum(row['simple_primitive_count'] for row in rows)}")
if len(starts) != 1: failures.append(f"expected one standing operator start, found {len(starts)}")
if len(nav_bounds) != 1: failures.append(f"expected one nav bounds volume, found {len(nav_bounds)}")
if len(authorities) != 1: failures.append(f"expected one native authority, found {len(authorities)}")
protected_hashes = {}
for name, (path, expected) in protected.items():
    actual = sha(path); protected_hashes[name] = actual
    if actual != expected: failures.append(f"protected {name} changed: {actual}")
report = {
    "$schema": "cairnwell/audit/press-train-a-physical-static-v018/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V018_EXACT_COLLISION_POLICY_OPERATOR_START_NAV_BOUNDS_AUTHORITY_AND_LINEAGE__PIE_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__V018_PHYSICAL_STATIC_GATE__NOT_PROMOTED",
    "map": map_path, "map_sha256": sha(map_file),
    "presentation_actor_count": len(presentation), "blocking_actor_count": len(blocking),
    "query_mover_count": len(query), "unlisted_visual_count": len(unlisted),
    "unlisted_collision_enabled": unlisted_enabled,
    "simple_primitive_total": sum(row["simple_primitive_count"] for row in rows),
    "policy_counts": dict(Counter(row["policy"] for row in rows)), "collision_rows": rows,
    "standing_operator_start_count": len(starts),
    "standing_operator_start_location_cm": ([starts[0].get_actor_location().x, starts[0].get_actor_location().y,
                                               starts[0].get_actor_location().z] if starts else None),
    "nav_bounds_volume_count": len(nav_bounds), "native_authority_count": len(authorities),
    "inherited_safety_collision_volumes": legacy_safety_volumes,
    "protected_map_hashes": protected_hashes, "failures": failures,
    "production_map_changed": False, "promotion_authorized": False,
}
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "blocking": len(blocking), "query": len(query),
                  "primitives": report["simple_primitive_total"]}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
