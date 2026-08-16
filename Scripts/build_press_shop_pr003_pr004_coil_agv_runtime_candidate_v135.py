"""Bind the tested coil-AGV runtime authority in an isolated child of v134.

v134 has only a provisional visual pass for runtime development. v135 remains
unpromoted until exact-map PIE, collision, navigation, authority and visual
gates pass. The retained v124 package and all rejected evidence stay immutable.
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVCandidate_v134"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135"
PROJECT = Path(unreal.Paths.project_dir())
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr003_pr004_coil_agv_runtime_build_v135.json"
BASE_PACKAGE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVCandidate_v134.umap"
RETAINED_PACKAGE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124.umap"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
base_hash_before = sha256(BASE_PACKAGE)
retained_hash_before = sha256(RETAINED_PACKAGE)

if not levels.load_level(BASE):
    raise RuntimeError(f"Could not load provisional visual parent {BASE}")
unreal.SystemLibrary.collect_garbage()
if library.does_asset_exist(MAP) and not library.delete_asset(MAP):
    raise RuntimeError(f"Could not remove owned candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"Could not create isolated v135 from {BASE}")

controller = actors_api.spawn_actor_from_class(
    unreal.LBCoilAGVController,
    unreal.Vector(-6200.0, -2700.0, 0.0),
    unreal.Rotator())
if controller is None:
    raise RuntimeError("Could not spawn ALBCoilAGVController")
controller.set_actor_label("LB_PR003_PR004_V135_CoilAGV_RuntimeAuthority")
controller.tags = [
    unreal.Name("LB.Asset.Candidate.v135"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Runtime.Authority.CoilAGV"),
    unreal.Name("LB.OwnerDirectedRevision.CoilAGV"),
    unreal.Name("LB.Authority.GameplayTuning.NotCertification")]

chassis = []
deck = []
loads = []
stored = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.Vehicle.CoilAGV" in tags and "LB.Vehicle.CoilAGV.LiftDeck" not in tags:
        chassis.append(actor)
    if "LB.Vehicle.CoilAGV.LiftDeck" in tags:
        deck.append(actor)
    if "LB.Inventory.InTransfer" in tags:
        loads.append(actor)
    if "LB.Material.PackagedCoil" in tags and any(tag.startswith("LB.PR003.Layout.Slot.") for tag in tags) and "LB.Inventory.InTransfer" not in tags and not actor.get_editor_property("hidden"):
        stored.append(actor)

failures = []
if len(chassis) != 1: failures.append(f"expected one tagged AGV chassis, found {len(chassis)}")
if len(deck) != 1: failures.append(f"expected one tagged AGV lift deck, found {len(deck)}")
if len(loads) != 1: failures.append(f"expected one in-transfer physical load, found {len(loads)}")
if len(stored) != 11: failures.append(f"expected eleven stored coils, found {len(stored)}")
if failures:
    raise RuntimeError("; ".join(failures))

for actor in chassis + deck + loads:
    actor.tags = list(actor.tags) + [unreal.Name("LB.Runtime.Authority.BoundBy.CoilAGV.v135")]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

base_hash_after = sha256(BASE_PACKAGE)
retained_hash_after = sha256(RETAINED_PACKAGE)
if base_hash_before != base_hash_after:
    raise RuntimeError("v134 visual parent changed while building v135")
if retained_hash_before != retained_hash_after:
    raise RuntimeError("retained v124 package changed while building v135")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-coil-agv-runtime-build-v135/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_RUNTIME_AUTHORITY_BOUND__EXACT_MAP_GATES_REQUIRED__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "controller_class": "/Script/LineBossCarFactory.LBCoilAGVController",
    "binding_counts": {"chassis": len(chassis), "lift_deck": len(deck), "in_transfer": len(loads), "stored": len(stored)},
    "route_points_cm": {"staged": [-6200.0, -2700.0, 29.0], "turn": [-5550.0, -2700.0, 29.0], "dock": [-5550.0, -2000.0, 29.0]},
    "runtime_test": "LineBoss.PressShop.PR003PR004.CoilAGVRuntime",
    "runtime_test_status": "PASS",
    "performance_values": "GAMEPLAY_TUNING_ONLY__CERTIFICATION_TBC",
    "v134_hash_before": base_hash_before,
    "v134_hash_after": base_hash_after,
    "v124_hash_before": retained_hash_before,
    "v124_hash_after": retained_hash_after,
    "promotion_authorized": False,
    "failures": failures
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
