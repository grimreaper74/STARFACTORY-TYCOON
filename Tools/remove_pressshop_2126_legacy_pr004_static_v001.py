"""Remove only superseded PR004 static art beneath the new 2126 front-end cell."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "remove_legacy_pr004_static_v001_receipt.json"
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
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    if not (-5200.0 <= loc.x <= -1000.0 and -5200.0 <= loc.y <= 1300.0):
        continue
    if label.startswith("LB_INT_PR004") or label.startswith("LB_PR004"):
        matches.append((actor, label))

if len(matches) != 156:
    raise RuntimeError(f"fail closed: expected exactly 156 PR004 static actors, matched {len(matches)}")
removed = []
for actor, label in matches:
    if not unreal.EditorLevelLibrary.destroy_actor(actor):
        raise RuntimeError(f"failed to remove superseded PR004 actor: {label}")
    removed.append(label)

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save PR004 cleanup")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

remaining = {a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
required = {
    "2126 FRONT END | autonomous decoiler straightener and servo feed",
    "2126 FRONT END | active feed coil",
}
if not required.issubset(remaining):
    raise RuntimeError(f"new front-end actors missing after cleanup: {sorted(required - remaining)}")
if any(label in remaining for label in removed):
    raise RuntimeError("one or more superseded PR004 static actors remain")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__LEGACY_PR004_STATIC_ART_REMOVED",
    "candidate_map": MAP,
    "removed_actor_count": len(removed),
    "removed_actor_labels": removed,
    "runtime_non_static_actors_preserved": True,
    "required_2126_actors_preserved": sorted(required),
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_PR004_STATIC_CLEAN_PASS count={len(removed)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
