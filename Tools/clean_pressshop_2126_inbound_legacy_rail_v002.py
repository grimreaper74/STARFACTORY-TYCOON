"""Hide the remaining legacy 30T rail/witness geometry crossing the 2126 unload cell."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "clean_inbound_legacy_rail_v002_receipt.json"
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

prefixes = ("LB_PR004_V031_30T_Rail", "LB_PR004_V113_30T_East_Back", "LB_PR004_V113_30T_West_Back")
hidden = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith(prefixes):
        actor.set_actor_hidden_in_game(True)
        try:
            actor.set_is_temporarily_hidden_in_editor(True)
        except Exception:
            pass
        hidden.append(label)
if len(hidden) != 4:
    raise RuntimeError(f"fail closed: expected four rail actors, matched {len(hidden)}: {hidden}")
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save cleaned candidate")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__REMAINING_LEGACY_RAIL_HIDDEN",
    "candidate_map": MAP,
    "hidden_actor_count": len(hidden),
    "hidden_actors": hidden,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_INBOUND_RAIL_CLEAN_PASS actors={hidden}")
unreal.SystemLibrary.quit_editor()
