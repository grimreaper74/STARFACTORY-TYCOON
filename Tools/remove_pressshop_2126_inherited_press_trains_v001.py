"""Remove the four inherited press-train groups from the isolated 2126 candidate."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "remove_inherited_press_trains_v001_receipt.json"
PREFIXES = ("LB_INST_PTA_", "LB_INST_PTB_", "LB_INST_PTC_", "LB_INST_PTD_")
EXPECTED = 1352
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest().lower()

before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected: raise RuntimeError(f"protected map missing or changed: {path}")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP): raise RuntimeError("could not load isolated 2126 candidate")

targets = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith(PREFIXES)]
if len(targets) != EXPECTED: raise RuntimeError(f"expected {EXPECTED} inherited press-train actors, found {len(targets)}")
by_prefix, by_class, samples = Counter(), Counter(), []
for actor in targets:
    label = actor.get_actor_label()
    prefix = next(p for p in PREFIXES if label.startswith(p))
    by_prefix[prefix] += 1; by_class[actor.get_class().get_name()] += 1
    if len(samples) < 20: samples.append({"label":label,"class":actor.get_class().get_name()})
    unreal.EditorLevelLibrary.destroy_actor(actor)

remaining = [a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith(PREFIXES)]
if remaining: raise RuntimeError(f"inherited train actors remain: {remaining[:10]}")
new_labels = [a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith("2126 ")]
if len(new_labels) < 27: raise RuntimeError(f"new 2126 actor set unexpectedly small after deletion: {len(new_labels)}")

if not unreal.EditorLoadingAndSavingUtils.save_current_level(): raise RuntimeError("inherited train removal did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before: raise RuntimeError("protected maps changed during inherited train removal")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status":"PASS__FOUR_INHERITED_PRESS_TRAINS_REMOVED_FROM_ISOLATED_2126_CANDIDATE",
    "map":MAP,
    "removed_count":len(targets),
    "removed_by_prefix":dict(sorted(by_prefix.items())),
    "removed_by_class":dict(sorted(by_class.items())),
    "samples":samples,
    "new_2126_actor_count_after":len(new_labels),
    "new_2126_actor_labels_after":sorted(new_labels),
    "protected_sha256_before":before,
    "protected_sha256_after":after,
},indent=2,sort_keys=True)+"\n",encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_INHERITED_TRAINS_REMOVAL_PASS count={len(targets)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
