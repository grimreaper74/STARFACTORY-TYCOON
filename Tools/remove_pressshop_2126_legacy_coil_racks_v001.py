"""Remove redundant legacy coil bays and their corridor fence from the isolated 2126 clone."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "remove_legacy_coil_racks_v001_receipt.json"
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
    raise RuntimeError("could not load isolated 2126 candidate")

matches = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    if not (-8100.0 <= loc.x <= -5000.0 and -5200.0 <= loc.y <= 1300.0):
        continue
    old_coil_bay = (
        label.startswith("LB_INT_FRONT_CS-")
        or label.startswith("LB_COIL_LABEL_V026_LB_INT_FRONT_CS-")
        or label.startswith("LB_COIL_TRACE_PANEL_V039_LB_INT_FRONT_CS-")
    )
    old_corridor_wall = label.startswith("LB_INT_FRONT_PR001_EastBoundary_")
    if old_coil_bay or old_corridor_wall:
        matches.append((actor, label, "legacy_coil_bay" if old_coil_bay else "superseded_corridor_wall"))

if len(matches) != 160:
    raise RuntimeError(f"fail closed: expected exactly 160 superseded actors, matched {len(matches)}")
removed = []
for actor, label, reason in matches:
    if not unreal.EditorLevelLibrary.destroy_actor(actor):
        raise RuntimeError(f"failed to remove {label}")
    removed.append({"label": label, "reason": reason})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save corridor cleanup")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

remaining = {a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
still_present = [row["label"] for row in removed if row["label"] in remaining]
if still_present:
    raise RuntimeError(f"removed actors still present: {still_present}")
required = {
    "2126 COIL | autonomous verification and de-banding cell",
    "2126 COIL | magnetic three-position buffer shuttle",
    "2126 COIL | verification cell active load",
    "2126 COIL | magnetic buffer load A",
    "2126 COIL | magnetic buffer load C",
}
if not required.issubset(remaining):
    raise RuntimeError(f"new 2126 corridor actors missing after cleanup: {sorted(required - remaining)}")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__LEGACY_COIL_RACKS_AND_WALL_REMOVED",
    "candidate_map": MAP,
    "removed_actor_count": len(removed),
    "legacy_coil_bay_actor_count": sum(1 for row in removed if row["reason"] == "legacy_coil_bay"),
    "superseded_corridor_wall_actor_count": sum(1 for row in removed if row["reason"] == "superseded_corridor_wall"),
    "required_2126_actors_preserved": sorted(required),
    "removed_actors": removed,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_COIL_RACK_CLEAN_PASS count={len(removed)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
