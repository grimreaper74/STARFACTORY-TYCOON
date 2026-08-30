"""Refine the registered 2126 press-train installation in the isolated map.

This pass removes only exact, audited legacy service-fleet actors and the two
superseded ladder-like guide rails. The registered sprite master, native
collision proxies, three animated transfer shuttles, lighting, and protected
authority maps are preserved.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MASTER_LABEL = "2126 PRESS | registered continuous S01-S04 master sprite"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "registered_master_refinement_v002_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.RegisteredMasterTrain.v002")
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap":
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap":
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

# These were identified by the read-only service-lane audit. They are old
# wheeled/red service-fleet presentation and its runtime spawner, not part of
# the 2126 hover/magnetic visual contract.
LEGACY_SERVICE_ACTORS = (
    "BP_LB_CR01_CleaningAMR_v0640",
    "BP_LB_CR01_CleaningAMR_v0641",
    "LB-CR01-01",
    "LB-CR01-02",
    "LB-DOCK-CR01-01",
    "LB-DOCK-CR01-02",
    "LB_SUPPORT_FLEET_RUNTIME_AUTHORITY_v269",
)

# The registered master contains its own continuous transfer datum. These two
# black ladder shapes were an early blockout and are visually misleading.
SUPERSEDED_GUIDE_RAILS = (
    "2126 TRANSFER | floor guide rail operator",
    "2126 TRANSFER | floor guide rail service",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected authority missing or changed: " + str(path))
if RECEIPT.exists():
    raise RuntimeError("registered-master refinement receipt already exists; refusing overwrite")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
master = by_label.get(MASTER_LABEL)
if not isinstance(master, unreal.StaticMeshActor):
    raise RuntimeError("registered press-train master is missing")
if not master.static_mesh_component.is_visible():
    raise RuntimeError("registered press-train master is not visible")
if "NO_COLLISION" not in str(master.static_mesh_component.get_collision_enabled()).upper():
    raise RuntimeError("registered master must remain visual-only")

removed = []
for label in LEGACY_SERVICE_ACTORS + SUPERSEDED_GUIDE_RAILS:
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError("audited actor missing before refinement: " + label)
    removed.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [
            float(actor.get_actor_location().x),
            float(actor.get_actor_location().y),
            float(actor.get_actor_location().z),
        ],
    })
    if not unreal.EditorLevelLibrary.destroy_actor(actor):
        raise RuntimeError("could not remove audited actor: " + label)

master.tags = list(master.tags) + [TAG]

# Preserve and explicitly verify the gameplay-facing pieces that sit behind
# the one-piece visual master.
remaining = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
for entry in removed:
    if entry["label"] in remaining:
        raise RuntimeError("removed actor still exists: " + entry["label"])

collision_labels = [
    "2126 COLLISION | S01 deep draw",
    "2126 COLLISION | S02 redraw calibration",
    "2126 COLLISION | S03 trim pierce",
    "2126 COLLISION | S04 flange final form",
]
shuttle_labels = [
    f"2126 TRANSFER | magnetic panel shuttle sprite {index}" for index in range(1, 4)
]
for label in collision_labels + shuttle_labels:
    if label not in remaining:
        raise RuntimeError("required native gameplay actor missing after refinement: " + label)

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("refined candidate map did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during registered-master refinement")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__REGISTERED_MASTER_REFINED_AND_LEGACY_CLUTTER_REMOVED",
    "map": MAP,
    "master_actor": MASTER_LABEL,
    "removed_exact_actors": removed,
    "removed_legacy_service_actor_count": len(LEGACY_SERVICE_ACTORS),
    "removed_superseded_guide_rail_count": len(SUPERSEDED_GUIDE_RAILS),
    "preserved_native_station_collision_proxies": collision_labels,
    "preserved_native_transfer_shuttles": shuttle_labels,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_REGISTERED_MASTER_REFINEMENT_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
