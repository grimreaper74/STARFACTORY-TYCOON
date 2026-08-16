"""Install the repaired six-part S07 unload robot on all four clean press trains."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069"
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_connected_s07_placement_v20260809_v791.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
DEST = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v788/S07ConnectedVacuumTool"
ROWS = {"A": -3300.0, "B": -1100.0, "C": 1100.0, "D": 3300.0}
ROBOT_X, ROBOT_Y_OFFSET, ROBOT_Z = 8600.0, 420.0, 130.0

sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
before = sha(PROTECTED)
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if before != EXPECTED or lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("fresh/protected invariant")

def role(path):
    lower = path.lower()
    mapping = {
        "s07_base": "BASE",
        "s07_turn": "TURN",
        "s07_lower": "LOWER",
        "s07_upper": "UPPER",
        "s07_wrist": "WRIST",
        "s07_tool": "TOOL",
    }
    matches = [value for fragment, value in mapping.items() if fragment in lower]
    if len(matches) != 1:
        raise RuntimeError("unknown/ambiguous S07 role: " + path)
    return matches[0]

items = []
for path in lib.list_assets(DEST, recursive=True, include_folder=False):
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        items.append((role(path), asset, path))
if len(items) != 6 or len({item[0] for item in items}) != 6:
    raise RuntimeError(f"Expected six unique segmented meshes, got {len(items)}")
if not levels.new_level_from_template(MAP, SOURCE):
    raise RuntimeError("map child failed")

placeholder_labels = {f"LB_CLEAN_Train{train}_S07_UnloadRobot" for train in ROWS}
removed = []
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() in placeholder_labels:
        removed.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        })
        if not actors.destroy_actor(actor):
            raise RuntimeError("failed to remove " + actor.get_actor_label())
if {item["label"] for item in removed} != placeholder_labels:
    raise RuntimeError({"expected": sorted(placeholder_labels), "removed": removed})

parent_role = {
    "BASE": None,
    "TURN": "BASE",
    "LOWER": "TURN",
    "UPPER": "LOWER",
    "WRIST": "UPPER",
    "TOOL": "WRIST",
}
created, bounds = [], {}
for train, row_y in ROWS.items():
    by_role = {}
    location = unreal.Vector(ROBOT_X, row_y + ROBOT_Y_OFFSET, ROBOT_Z)
    for component_role, mesh, path in items:
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator())
        actor.set_actor_label(f"LB_CLEAN_Train{train}_S07_ConnectedRobot_{component_role}_v791")
        actor.tags = [unreal.Name(tag) for tag in [
            "LB.CleanRebuild.v20260809.v791", f"LB.PressTrain.{train}", "LB.Station.S07",
            "LB.S07Robot.UserSegmented.v787", f"LB.S07Robot.Component.{component_role}",
            f"LB.S07Robot.Parent.{parent_role[component_role] or 'WORLD'}",
            "LB.S07Robot.Tool.ConnectedVacuumFrameEightCups", "LB.Source.NoLegacyMapCopy",
        ]]
        component = actor.static_mesh_component
        component.set_static_mesh(mesh)
        component.set_mobility(unreal.ComponentMobility.STATIC if component_role == "BASE" else unreal.ComponentMobility.MOVABLE)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if component_role == "BASE" else unreal.CollisionEnabled.QUERY_ONLY)
        component.set_editor_property("can_ever_affect_navigation", component_role == "BASE")
        by_role[component_role] = actor
        created.append({"train": train, "role": component_role, "label": actor.get_actor_label(), "asset": path})
    for component_role, parent in parent_role.items():
        if parent and not by_role[component_role].attach_to_actor(
            by_role[parent], unreal.Name(""), unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False
        ):
            raise RuntimeError(f"attach failed {train} {component_role}->{parent}")
    mins, maxs = [1e30] * 3, [-1e30] * 3
    for actor in by_role.values():
        origin, extent = actor.get_actor_bounds(False)
        values = [origin.x, origin.y, origin.z]
        exts = [extent.x, extent.y, extent.z]
        for axis, (value, ext) in enumerate(zip(values, exts)):
            mins[axis] = min(mins[axis], value - ext)
            maxs[axis] = max(maxs[axis], value + ext)
    bounds[train] = {"min_cm": mins, "max_cm": maxs, "size_cm": [maxs[i] - mins[i] for i in range(3)]}

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("save failed")
after = sha(PROTECTED)
failures = []
if after != before:
    failures.append("protected v438 changed")
if len(created) != 24:
    failures.append(f"created {len(created)} expected 24")
for train, bound in bounds.items():
    if bound["min_cm"][2] < -2.0:
        failures.append(f"{train} below floor {bound['min_cm'][2]:.3f}")
    if not 350.0 < bound["size_cm"][2] < 500.0:
        failures.append(f"{train} height unexpected {bound['size_cm'][2]:.3f}")

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791.umap"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_BUILD__FOUR_CONNECTED_S07_HIERARCHIES_INSTALLED__VISUAL_AND_MOTION_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__CLEAN_CONNECTED_S07_V791",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE, "map": MAP, "map_sha256": sha(map_file),
    "removed": removed, "created_count": len(created), "created": created,
    "hierarchy": parent_role, "bounds": bounds, "failures": failures,
    "meshy_credits_used": 0,
    "protected_v438_before": before, "protected_v438_after": after,
}, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_CLEAN_CONNECTED_S07_V791_PASS")
