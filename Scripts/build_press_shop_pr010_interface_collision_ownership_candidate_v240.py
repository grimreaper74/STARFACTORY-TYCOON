"""Build an isolated v240 child resolving duplicate PR010/Train B-C collision ownership.

The accepted PR010 presentation remains unchanged and owns collision in its
handoff footprint. Only the eleven provisional EST-P train presentation actors
identified by the read-only v239 AABB screen lose collision/navigation
relevance. Visible geometry, transforms, machine authority and runtime logic do
not change.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v240"
SOURCE_AUDIT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v239_restored_train_collision_overlap.json"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr010_interface_collision_ownership_build_v240.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239.umap"
STABLE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236.umap"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


source = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
target_labels = sorted({row["train_actor"] for row in source["overlaps"]})
if len(target_labels) != 11:
    raise RuntimeError(f"expected exactly eleven classified train interface actors, found {len(target_labels)}")
if any(not (label.startswith("LB_INST_PTB_") or label.startswith("LB_INST_PTC_")) for label in target_labels):
    raise RuntimeError("contact target escaped provisional Train B/C presentation")
if any("_S01_" not in label and "CommonFoundation" not in label and "TransferRail" not in label
       for label in target_labels):
    raise RuntimeError("contact target escaped the classified S01 interface")

protected_before = {"v236": sha256(STABLE_FILE), "v239": sha256(BASE_FILE)}
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors_by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
changes = []
failures = []
for label in target_labels:
    actor = actors_by_label.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        failures.append(f"missing expected static presentation actor {label}")
        continue
    component = actor.static_mesh_component
    before_collision = str(component.get_collision_enabled())
    try:
        before_navigation = bool(component.get_editor_property("can_ever_affect_navigation"))
    except Exception:
        before_navigation = None
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    prior_tags = [str(value) for value in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
        "LB.Asset.Candidate.v240",
        "LB.Collision.InterfaceOwnedBy.PR010.v240",
        "LB.Navigation.InterfaceOwnedBy.PR010.v240",
        "LB.LayoutAuthority.EST-P.ReferenceOnly",
        "LB.Asset.CandidateNotPromoted",
    ])]
    changes.append({
        "label": label,
        "before_collision": before_collision,
        "after_collision": str(component.get_collision_enabled()),
        "before_navigation": before_navigation,
        "after_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        "visible_geometry_transform_material_changed": False,
    })

if len(changes) != 11:
    failures.append(f"expected eleven interface ownership changes, made {len(changes)}")
if any(row["after_collision"] != str(unreal.CollisionEnabled.NO_COLLISION) for row in changes):
    failures.append("one or more interface actors retained collision")
if any(row["after_navigation"] for row in changes):
    failures.append("one or more interface actors retained navigation relevance")
if not levels.save_current_level():
    failures.append("could not save v240")

protected_after = {"v236": sha256(STABLE_FILE), "v239": sha256(BASE_FILE)}
if protected_before != protected_after:
    failures.append("protected parent or stable baseline changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v240.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-pr010-interface-collision-ownership-build-v240/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ACCEPTED_PR010_OWNS_INTERFACE_COLLISION__EXACT_GATES_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "source_contact_audit": str(SOURCE_AUDIT.relative_to(ROOT)).replace("\\", "/"),
    "protected_sha256_before": protected_before,
    "protected_sha256_after": protected_after,
    "map_sha256": sha256(map_file) if map_file.exists() else None,
    "changed_actor_count": len(changes),
    "changed_actors": changes,
    "accepted_pr009_pr010_actor_transform_material_collision_changes": 0,
    "visible_geometry_transform_material_changes": 0,
    "machine_or_runtime_authority_changes": 0,
    "engineering_datums_invented": 0,
    "collision_owner": "ACCEPTED_PR010_PRESENTATION_IN_MASTER_PLAN_HANDOFF_FOOTPRINT",
    "yielding_scope": "ELEVEN_PROVISIONAL_EST-P_TRAIN_B_C_S01_INTERFACE_PRESENTATION_ACTORS",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()

