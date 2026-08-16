"""Fresh v356 child adding dedicated Press Train A-D navigation coverage."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356"
MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_expanded_train_nav_build_v362.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Refusing to overwrite v362")
base_before = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("Could not create fresh v362 child")

# Covers the completed four-line block and its three widened longitudinal
# aisles, without reaching the distant support-fleet berth volume.
bounds = actors.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume, unreal.Vector(3850.0, -1000.0, 350.0), unreal.Rotator())
if bounds is None:
    raise RuntimeError("Could not spawn train navigation bounds")
bounds.set_actor_label("LB_PRESS_TRAINS_V362_NavBounds_ExpandedBlock")
bounds.set_actor_scale3d(unreal.Vector(33.0, 37.5, 3.5))
bounds.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v362", "LB.Asset.CandidateNotPromoted",
    "LB.PressTrains.Navigation", "LB.Navigation.LocalCoverage",
    "LB.Navigation.ExpandedTrainBlock.v362")]

for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)

origin, extent = bounds.get_actor_bounds(False, False)
failures = []
size = [extent.x * 2, extent.y * 2, extent.z * 2]
if not (6500 <= size[0] <= 6700 and 7400 <= size[1] <= 7600 and 690 <= size[2] <= 710):
    failures.append(f"unexpected navigation bounds size {size}")
if not levels.save_current_level():
    failures.append("v362 save failed")
base_after = sha(BASE_FILE)
if base_before != base_after:
    failures.append("protected v356 hash drift")

payload = {
    "$schema": "cairnwell/audit/press-shop-expanded-train-nav-build-v362/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DEDICATED_EXPANDED_TRAIN_NAV_COVERAGE_AUTHORED__EXACT_PIE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_RETAINED",
    "base": BASE, "map": MAP,
    "base_sha256_before": base_before, "base_sha256_after": base_after,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "navigation_bounds": {"label": bounds.get_actor_label(), "origin_cm": [origin.x, origin.y, origin.z], "size_cm": size},
    "visible_geometry_changes": 0, "collision_policy_changes": 0,
    "runtime_authority_changes": 0, "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
