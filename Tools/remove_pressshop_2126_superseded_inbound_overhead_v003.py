"""Permanently remove superseded inbound overhead actors from the isolated candidate clone."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "remove_superseded_inbound_overhead_v003_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated full-hall candidate")

remove = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    if not (-11000.0 <= loc.x <= -6500.0 and -5500.0 <= loc.y <= 1300.0):
        continue
    asset = ""
    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp and comp.static_mesh:
            asset = comp.static_mesh.get_path_name()
    except Exception:
        pass
    old_crane = "/MaterialHandling/BridgeCrane/" in asset
    old_roof_beam = label.startswith("LB_PR004_V028_RoofBeam_")
    old_rail = label.startswith(("LB_PR004_V031_30T_Rail", "LB_PR004_V113_30T_East_Back", "LB_PR004_V113_30T_West_Back"))
    if old_crane or old_roof_beam or old_rail:
        remove.append((actor, label, asset))

if len(remove) != 38:
    raise RuntimeError(f"fail closed: expected exactly 38 superseded actors, matched {len(remove)}")
removed = []
for actor, label, asset in remove:
    if not unreal.EditorLevelLibrary.destroy_actor(actor):
        raise RuntimeError(f"failed to remove superseded actor: {label}")
    removed.append({"label": label, "asset": asset})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save candidate after actor removal")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

remaining_labels = {a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
still_present = [row["label"] for row in removed if row["label"] in remaining_labels]
if still_present:
    raise RuntimeError(f"removed actors still present: {still_present}")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__SUPERSEDED_INBOUND_OVERHEAD_REMOVED",
    "candidate_map": MAP,
    "removed_actor_count": len(removed),
    "removed_actors": removed,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_INBOUND_REMOVE_PASS count={len(removed)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
