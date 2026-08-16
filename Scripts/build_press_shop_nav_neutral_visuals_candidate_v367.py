"""Fresh v362 child: prevent NoCollision visual components dirtying navmesh."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362"
MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_nav_neutral_visuals_build_v367.json"
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
    raise RuntimeError("Refusing to overwrite v367")
before = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("Could not create v367")

changed = []
by_actor_class = Counter()
for actor in actors.get_all_level_actors():
    count = 0
    for comp in actor.get_components_by_class(unreal.PrimitiveComponent):
        try:
            affects = bool(comp.get_editor_property("can_ever_affect_navigation"))
        except Exception:
            continue
        if affects and comp.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
            comp.set_editor_property("can_ever_affect_navigation", False)
            count += 1
    if count:
        changed.append({"actor": actor.get_actor_label(), "class": actor.get_class().get_name(), "component_count": count})
        by_actor_class[actor.get_class().get_name()] += count

failures = []
if sum(row["component_count"] for row in changed) < 756:
    failures.append("expected at least the 756 audited MR01 NoCollision visual components")
if not levels.save_current_level():
    failures.append("v367 save failed")
after = sha(BASE_FILE)
if before != after:
    failures.append("protected v362 hash drift")
payload = {"$schema": "cairnwell/audit/press-shop-nav-neutral-visuals-build-v367/v1",
           "generated_utc": datetime.now(timezone.utc).isoformat(),
           "status": "PASS__NO_COLLISION_VISUALS_NAV_NEUTRALIZED__EXACT_WHOLE_SHOP_PIE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_RETAINED",
           "base": BASE, "map": MAP, "base_sha256_before": before, "base_sha256_after": after,
           "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
           "changed_component_count": sum(row["component_count"] for row in changed),
           "changed_by_actor_class": dict(by_actor_class), "changed_actors": changed,
           "collision_enabled_changes": 0, "visible_geometry_changes": 0,
           "runtime_authority_changes": 0, "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
