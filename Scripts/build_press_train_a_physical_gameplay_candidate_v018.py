"""Build isolated Train A v018 with deterministic player and sensing collision."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
parent_map = "/Game/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017"
target_map = "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v018"
dest = "/Game/LineBoss/Candidates/PressTrains/TrainA/PhysicalGameplay_v018"
collision_dest = dest + "/CollisionMeshes"
plan_path = root / "Saved/Audits/PressTrains/press_train_a_collision_plan_v018.json"
out = root / "Saved/Audits/PressTrains/press_train_a_physical_gameplay_build_v018.json"
parent_file = root / "Content/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017.umap"
target_file = root / "Content/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v018.umap"
protected = {
    "v017": (parent_file, "E647EB62C3552CF39EFFE83687C2A3AA058C0323F2DD53DACFD5FD0738B02E42"),
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


def add_tags(actor, *values):
    current = [str(value) for value in actor.tags]
    for value in values:
        if value not in current:
            current.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in current])


def collision_counts(mesh):
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    counts = {
        "box": len(agg.get_editor_property("box_elems")),
        "sphere": len(agg.get_editor_property("sphere_elems")),
        "capsule": len(agg.get_editor_property("sphyl_elems")),
        "convex": len(agg.get_editor_property("convex_elems")),
    }
    counts["total"] = sum(counts.values())
    return counts


def apply_boxes(mesh, specs):
    body = mesh.get_editor_property("body_setup")
    agg = unreal.KAggregateGeom()
    elements = []
    for spec in specs:
        element = unreal.KBoxElem()
        element.set_editor_property("center", unreal.Vector(*spec["center_cm"]))
        element.set_editor_property("rotation", unreal.Rotator(*spec["rotation_degrees"]))
        element.set_editor_property("x", spec["dimensions_cm"][0])
        element.set_editor_property("y", spec["dimensions_cm"][1])
        element.set_editor_property("z", spec["dimensions_cm"][2])
        elements.append(element)
    agg.set_editor_property("box_elems", elements)
    body.set_editor_property("agg_geom", agg)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body.modify(); mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    counts = collision_counts(mesh)
    if counts != {"box": len(specs), "sphere": 0, "capsule": 0, "convex": 0, "total": len(specs)}:
        raise RuntimeError(f"Collision persistence mismatch for {mesh.get_path_name()}: {counts}")
    return counts


plan = json.loads(plan_path.read_text(encoding="utf-8"))
if not plan["status"].startswith("PASS__V018_AUTHORED_GEOMETRY_COLLISION_PLAN"):
    raise RuntimeError("v018 source collision plan is not a PASS")
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(target_map) or library.does_directory_exist(dest) or out.exists():
    raise RuntimeError("Refusing to overwrite Train A physical-gameplay v018")
parent_hash = sha(parent_file)
if parent_hash != protected["v017"][1]:
    raise RuntimeError(f"retained v017 changed before build: {parent_hash}")
if not levels.new_level_from_template(target_map, parent_map):
    raise RuntimeError("Could not create v018 from retained v017")

all_actors = actors_api.get_all_level_actors()
for actor in all_actors:
    add_tags(actor, "LB.PressTrain.TrainA.PhysicalGameplay.v018", "LB.Asset.Candidate.v018",
             "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented")

planned = {row["object"]: row for row in plan["actors"]}
asset_cache = {}
rows = []
for actor in all_actors:
    label = actor.get_actor_label()
    source_name = label.removesuffix("_UEv017")
    spec = planned.get(source_name)
    if spec is None:
        continue
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError(f"planned actor is not StaticMeshActor: {label}")
    component = actor.static_mesh_component
    old_mesh = component.get_editor_property("static_mesh")
    if old_mesh is None:
        raise RuntimeError(f"planned actor has no mesh: {label}")
    signature_payload = json.dumps({"mesh": old_mesh.get_path_name(), "policy": spec["policy"],
                                    "boxes": spec["boxes"]}, sort_keys=True).encode("utf-8")
    signature = hashlib.sha256(signature_payload).hexdigest().upper()[:12]
    cache_key = (old_mesh.get_path_name(), signature)
    if cache_key not in asset_cache:
        target_asset = f"{collision_dest}/{old_mesh.get_name()}_{spec['policy']}_{signature}_v018"
        if not library.duplicate_asset(old_mesh.get_path_name().split(".")[0], target_asset):
            raise RuntimeError(f"Could not duplicate collision mesh {old_mesh.get_path_name()}")
        new_mesh = library.load_asset(target_asset)
        counts = apply_boxes(new_mesh, spec["boxes"])
        asset_cache[cache_key] = (new_mesh, counts)
    new_mesh, counts = asset_cache[cache_key]
    component.set_static_mesh(new_mesh)
    if spec["policy"] == "BLOCK_ALL":
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        add_tags(actor, "LB.Collision.TrainA.Blocking.v018")
    else:
        component.set_collision_profile_name(unreal.Name("OverlapAllDynamic"))
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        add_tags(actor, "LB.Collision.TrainA.QueryMover.v018")
    component.set_editor_property("can_ever_affect_navigation", bool(spec["nav_relevant"]))
    actor.set_actor_label(source_name + "_UEv018")
    rows.append({
        "actor": actor.get_actor_label(), "source_actor": label, "role": spec["role"],
        "policy": spec["policy"], "nav_relevant": bool(spec["nav_relevant"]),
        "source_mesh": old_mesh.get_path_name(), "collision_mesh": new_mesh.get_path_name(),
        "simple_collision": counts,
    })

if len(rows) != plan["planned_actor_count"]:
    raise RuntimeError(f"Expected {plan['planned_actor_count']} collision actors, found {len(rows)}")

# The start is on the authored positive-X operator aisle, on top of the 25 cm
# foundation.  Z is derived from floor top + the authoritative 88 cm capsule
# half-height; it is not a global factory-placement claim.
player_start = actors_api.spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(680.0, 600.0, 113.0), unreal.Rotator(0.0, 180.0, 0.0)
)
player_start.set_actor_label("CA_MW_PTA_OperatorAisle_PlayerStart_v018")
add_tags(player_start, "LB.PlayerStart.StandingOperator", "LB.PressTrain.TrainA.OperatorAisle",
         "LB.Asset.Candidate.v018", "LB.Authority.LocalPlacement.DerivedFromAuthoredAisle")

authorities = [actor for actor in all_actors if isinstance(actor, unreal.LBPressTrainAStation)]
nav_bounds = [actor for actor in all_actors if isinstance(actor, unreal.NavMeshBoundsVolume)]
if len(authorities) != 1 or len(nav_bounds) != 1:
    raise RuntimeError(f"authority/nav cardinality mismatch authority={len(authorities)} nav={len(nav_bounds)}")
nav_origin, nav_extent = nav_bounds[0].get_actor_bounds(False, False)

if not levels.save_current_level():
    raise RuntimeError("Could not save Train A physical-gameplay v018")
library.save_directory(dest, only_if_is_dirty=False, recursive=True)
if not target_file.exists():
    raise RuntimeError("v018 map missing after save")

failures = []
protected_hashes = {}
for name, (path, expected) in protected.items():
    actual = sha(path); protected_hashes[name] = actual
    if actual != expected:
        failures.append(f"protected {name} changed: {actual}")
policy_counts = Counter(row["policy"] for row in rows)
report = {
    "$schema": "cairnwell/audit/press-train-a-physical-gameplay-build-v018/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V018_AUTHORED_SIMPLE_COLLISION_AND_STANDING_OPERATOR_START__PIE_AND_NAVIGATION_GATES_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__V018_PHYSICAL_GAMEPLAY_BUILD__NOT_PROMOTED",
    "parent_map": parent_map, "parent_map_sha256": parent_hash,
    "target_map": target_map, "target_map_sha256": sha(target_file),
    "collision_plan": plan_path.relative_to(root).as_posix(),
    "collision_actor_count": len(rows), "collision_asset_count": len(asset_cache),
    "collision_box_total": sum(row["simple_collision"]["total"] for row in rows),
    "policy_actor_counts": dict(sorted(policy_counts.items())), "actors": rows,
    "standing_player_start": {"actor": player_start.get_actor_label(),
        "location_cm": [680.0, 600.0, 113.0], "capsule_radius_cm": 34.0,
        "capsule_half_height_cm": 88.0, "floor_top_cm": 25.0,
        "placement_authority": "authored positive-X operator aisle; local isolated-map placement"},
    "nav_bounds": {"actor": nav_bounds[0].get_actor_label(),
        "origin_cm": [nav_origin.x, nav_origin.y, nav_origin.z],
        "extent_cm": [nav_extent.x, nav_extent.y, nav_extent.z]},
    "native_authority_count": len(authorities), "protected_map_hashes": protected_hashes,
    "visual_geometry_changed": False, "materials_changed": False, "lighting_changed": False,
    "production_map_changed": False, "failures": failures, "promotion_authorized": False,
}
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "collision_actors": len(rows),
                  "collision_assets": len(asset_cache), "boxes": report["collision_box_total"]}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
