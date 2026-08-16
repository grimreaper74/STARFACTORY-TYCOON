"""Add support-fleet service-aisle nav coverage in a fresh v260 child."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v260"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v261"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v260.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v261.umap"
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_navigation_build_v261.json"

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LIB = unreal.EditorAssetLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if LIB.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {MAP}")
base_hash_before = sha256(BASE_FILE)
if not LEVELS.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"Could not derive {MAP} from {BASE}")

# Covers only the retained north support berths, their straight aprons and the
# common service aisle. Existing collision blockers carve the accessible floor.
nav_bounds = ACTORS.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume, unreal.Vector(-3350.0, 4650.0, 350.0), unreal.Rotator())
if nav_bounds is None:
    raise RuntimeError("Could not create support-fleet navigation bounds")
nav_bounds.set_actor_label("LB_SUPPORT_FLEET_NavBounds_ServiceAisle_v261")
nav_bounds.set_actor_scale3d(unreal.Vector(38.0, 8.0, 3.5))
nav_bounds.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v261",
    "LB.Asset.CandidateNotPromoted",
    "LB.SupportRobot.Navigation",
    "LB.Navigation.LocalCoverage",
    "LB.Navigation.SupportServiceAisle.v261",
)]

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
recast = [actor for actor in ACTORS.get_all_level_actors() if isinstance(actor, unreal.RecastNavMesh)]
for actor in recast:
    actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
    actor.set_editor_property("can_be_main_nav_data", True)

origin, extent = nav_bounds.get_actor_bounds(False, False)
failures = []
if len(recast) != 1:
    failures.append(f"expected one RecastNavMesh, found {len(recast)}")
if not LEVELS.save_current_level():
    failures.append("could not save v261")

base_hash_after = sha256(BASE_FILE)
if base_hash_before != base_hash_after:
    failures.append("protected v260 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-navigation-build-v261/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__LOCAL_SUPPORT_SERVICE_NAV_COVERAGE_ADDED__EXACT_PIE_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__NOT_RETAINED",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "navigation_bounds": {
        "actor": nav_bounds.get_actor_label(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "size_cm": [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0],
    },
    "recast_nav_mesh_count": len(recast),
    "visible_geometry_changes": 0,
    "robot_state_or_runtime_authority_changes": 0,
    "collision_policy_changes": 0,
    "engineering_data_invented": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
