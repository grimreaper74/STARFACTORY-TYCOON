"""Build an isolated bare-coil front-end candidate directly from accepted v006.

The accepted map and source mesh remain untouched.  A reusable bare-coil mesh is
duplicated from accepted Candidate_v006, receives authored simple collision, and
replaces only the obsolete wrapped MasterCoil actors in PR-001/PR-002/PR-003.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_BareCoilFrontEndCandidate_v021"
SOURCE_BARE_MESH = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v006/PackagingRig_v004/"
    "SM_LB_PR004_BareCoilCore_v004.SM_LB_PR004_BareCoilCore_v004"
)
DEST_BARE_MESH = (
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/"
    "SM_LB_BareMasterCoil_v021"
)
COIL_MATERIAL = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v006/Materials/"
    "MI_LB_PR004_CoilSteel.MI_LB_PR004_CoilSteel"
)
OUTPUT = (
    Path(unreal.Paths.project_saved_dir())
    / "Audits/press_shop_bare_coil_front_end_candidate_v021.json"
)

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def require_asset(path, expected_type):
    asset = unreal.load_asset(path)
    if asset is None or not isinstance(asset, expected_type):
        raise RuntimeError(f"Missing {expected_type.__name__}: {path}")
    return asset


if not lib.does_asset_exist(DEST_MAP):
    raise RuntimeError(f"Prepared candidate map is missing: {DEST_MAP}")
if not lib.does_asset_exist(DEST_BARE_MESH):
    raise RuntimeError(f"Prepared candidate mesh is missing: {DEST_BARE_MESH}")
bare_mesh = require_asset(DEST_BARE_MESH, unreal.StaticMesh)
coil_material = require_asset(COIL_MATERIAL, unreal.MaterialInterface)
body_setup = bare_mesh.get_editor_property("body_setup")
aggregate = body_setup.get_editor_property("agg_geom")
collision_counts = {
    field: len(aggregate.get_editor_property(field))
    for field in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")
}
if sum(collision_counts.values()) <= 0:
    raise RuntimeError("Reusable v021 bare coil has no simple collision")

if not levels.load_level(DEST_MAP):
    raise RuntimeError(f"Could not load {DEST_MAP}")

converted = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not (
        label.startswith("LB_INT_FRONT_CS-")
        or label == "LB_INT_FRONT_PR001-IN-01_MasterCoil"
        or label == "LB_INT_FRONT_PR002-QA-01_MasterCoil"
    ) or not label.endswith("_MasterCoil"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        raise RuntimeError(f"Target coil lacks StaticMeshComponent: {label}")
    old_mesh = component.get_editor_property("static_mesh")
    old_origin, old_extent = actor.get_actor_bounds(False)
    old_contact_z = old_origin.z - old_extent.z
    component.set_static_mesh(bare_mesh)
    component.set_material(0, coil_material)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    actor.set_actor_label(label.replace("MasterCoil", "BareMasterCoil_v021"))
    actor.tags = list(actor.tags) + [
        unreal.Name("LB.Asset.Candidate.v021"),
        unreal.Name("LB.Material.BareCoil"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    new_origin, new_extent = actor.get_actor_bounds(False)
    new_contact_z = new_origin.z - new_extent.z
    location = actor.get_actor_location()
    location.z += old_contact_z - new_contact_z
    actor.set_actor_location(location, False, False)
    final_origin, final_extent = actor.get_actor_bounds(False)
    final_contact_z = final_origin.z - final_extent.z
    converted.append({
        "label": actor.get_actor_label(),
        "source_mesh": old_mesh.get_path_name() if old_mesh else None,
        "candidate_mesh": bare_mesh.get_path_name(),
        "old_contact_z_cm": old_contact_z,
        "final_contact_z_cm": final_contact_z,
        "contact_delta_cm": final_contact_z - old_contact_z,
        "final_location_cm": [location.x, location.y, location.z],
    })

if len(converted) != 14:
    raise RuntimeError(f"Expected 14 obsolete front-end coils, converted {len(converted)}")
if any(abs(row["contact_delta_cm"]) > 0.05 for row in converted):
    raise RuntimeError("One or more replacement coils lost saddle contact height")
if not levels.save_current_level():
    raise RuntimeError("Could not save isolated v021 candidate map")

payload = {
    "$schema": "line-boss/audit/press-shop-bare-coil-front-end-candidate-v021/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_BARE_COIL_FRONT_END_CANDIDATE__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "candidate_map": DEST_MAP,
    "source_mesh": SOURCE_BARE_MESH,
    "candidate_mesh": bare_mesh.get_path_name(),
    "material": coil_material.get_path_name(),
    "collision_trace_flag": str(body_setup.get_editor_property("collision_trace_flag")),
    "simple_collision": collision_counts,
    "converted_actor_count": len(converted),
    "converted_actors": converted,
    "accepted_v006_preserved": True,
    "rejected_v007_v010_maps_used": False,
    "runtime_gate": "OPEN",
    "fresh_fixed_camera_visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_BARE_COIL_FRONT_END_V021_BUILD_PASS converted={len(converted)} "
    f"collision={collision_counts} output={OUTPUT}"
)
unreal.SystemLibrary.quit_editor()
