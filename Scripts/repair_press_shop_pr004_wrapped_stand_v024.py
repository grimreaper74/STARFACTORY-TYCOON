"""Correct v024 packaged-coil authority and remove a malformed floor prop."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
BAD_ACTOR = "LB_MOTH_V004_PR004_ServiceOil"
WRAPPED_MESH_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/SM_LB_MasterCoil_Candidate_v002"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_wrapped_stand_repair_v024.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
wrapped_mesh = lib.load_asset(WRAPPED_MESH_PATH)
if wrapped_mesh is None:
    raise RuntimeError(f"Missing wrapped packaged-coil mesh: {WRAPPED_MESH_PATH}")

repackaged = []
for coil_actor in list(actors.get_all_level_actors()):
    old_label = coil_actor.get_actor_label()
    if "BareMasterCoil_v021" not in old_label:
        continue
    component = coil_actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        raise RuntimeError(f"Stored bare coil lacks StaticMeshComponent: {old_label}")
    old_origin, old_extent = coil_actor.get_actor_bounds(False)
    old_bottom = old_origin.z - old_extent.z
    component.set_static_mesh(wrapped_mesh)
    component.set_editor_property("override_materials", [])
    new_origin, new_extent = coil_actor.get_actor_bounds(False)
    new_bottom = new_origin.z - new_extent.z
    correction = old_bottom - new_bottom
    location = coil_actor.get_actor_location()
    coil_actor.set_actor_location(unreal.Vector(location.x, location.y, location.z + correction), False, False)
    new_label = old_label.replace("BareMasterCoil_v021", "PackagedMasterCoil_v024")
    coil_actor.set_actor_label(new_label)
    coil_actor.tags = [
        unreal.Name("LB.Asset.Candidate.v024"),
        unreal.Name("LB.Material.PackagedCoil"),
        unreal.Name("LB.State.PackagedUntilPR004"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    repackaged.append({
        "actor": new_label,
        "mesh": wrapped_mesh.get_path_name(),
        "contact_height_correction_cm": correction,
        "world_bottom_before_cm": old_bottom,
        "world_bottom_after_cm": new_bottom + correction,
    })

if len(repackaged) != 14:
    raise RuntimeError(f"Expected 14 received/stored coils to be repackaged, changed {len(repackaged)}")

matches = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == BAD_ACTOR]
if len(matches) != 1:
    raise RuntimeError(f"Expected one malformed service-oil actor, found {len(matches)}")
actor = matches[0]
origin, extent = actor.get_actor_bounds(False)
evidence = {
    "actor": BAD_ACTOR,
    "mesh": [
        component.get_editor_property("static_mesh").get_path_name()
        for component in actor.get_components_by_class(unreal.StaticMeshComponent)
        if component.get_editor_property("static_mesh") is not None
    ],
    "bounds_origin_cm": [origin.x, origin.y, origin.z],
    "bounds_extent_cm": [extent.x, extent.y, extent.z],
    "bounds_bottom_cm": origin.z - extent.z,
    "reason": "Oversized rotated basic cylinder intended as service-oil dressing intersected the floor and rendered as a large beige wedge.",
}
actors.destroy_actor(actor)
if any(item.get_actor_label() == BAD_ACTOR for item in actors.get_all_level_actors()):
    raise RuntimeError("Malformed service-oil actor remains after destruction")
if not levels.save_current_level():
    raise RuntimeError("Could not save repaired v024 map")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-wrapped-stand-repair-v024/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "status": "PACKAGED_COIL_AUTHORITY_CORRECTED_AND_MALFORMED_FLOOR_PROP_REMOVED__FRESH_VISUAL_GATE_REQUIRED",
    "packaged_coil_authority": "All received/stored coils remain packaged; only the selected PR-004 interaction changes a coil to bare steel.",
    "repackaged_actor_count": len(repackaged),
    "repackaged_actors": sorted(repackaged, key=lambda item: item["actor"]),
    "removed": evidence,
    "accepted_v006_preserved": True,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR004_WRAPPED_STAND_V024_REPAIR_PASS repackaged={len(repackaged)} removed={BAD_ACTOR}"
)
unreal.SystemLibrary.quit_editor()
