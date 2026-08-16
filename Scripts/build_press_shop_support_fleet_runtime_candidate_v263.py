"""Install the native support-fleet authority in a fresh v262 child."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v262"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v263"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v262.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v263.umap"
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_runtime_build_v263.json"
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

controller = ACTORS.spawn_actor_from_class(
    unreal.LBPressShopSupportFleetController, unreal.Vector(-3300.0, 3000.0, 0.0), unreal.Rotator())
if controller is None:
    raise RuntimeError("Could not spawn native support-fleet controller")
controller.set_actor_label("LB_SUPPORT_FLEET_RUNTIME_AUTHORITY_v263")
controller.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v263",
    "LB.Asset.CandidateNotPromoted",
    "LB.Runtime.Authority.SupportFleet",
    "LB.SupportRobot.CertifiedRoutes.R01",
)]

if not LEVELS.save_current_level():
    raise RuntimeError("Could not save v263")
base_hash_after = sha256(BASE_FILE)
failures = []
if base_hash_before != base_hash_after:
    failures.append("protected v262 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-runtime-build-v263/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NATIVE_FOUR_UNIT_FLEET_AUTHORITY_INSTALLED__EXACT_PIE_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__NOT_RETAINED",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "controller_actor": controller.get_actor_label(),
    "controller_class": controller.get_class().get_path_name(),
    "visible_geometry_changes": 0,
    "collision_policy_changes": 0,
    "route_revision": 1,
    "route_engineering_status": "TBC_PENDING_EXACT_RUNTIME_GATE",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
