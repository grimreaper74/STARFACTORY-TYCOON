"""Hide superseded inbound crane/roof-beam actors in the isolated 2126 candidate only."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
EXPECTED_SHA256 = "9fafc8fc98df14c9a72db21e14b39a60ee45fc5e0a5e04824e23f821d2edc280"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "clean_inbound_legacy_overhead_v001_receipt.json"
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
if digest(MAP_FILE) != EXPECTED_SHA256:
    raise RuntimeError("candidate map changed since the unload-gantry pass")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated full-hall candidate")

hidden = []
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
    superseded_crane = "/MaterialHandling/BridgeCrane/" in asset
    superseded_roof_grid = label.startswith("LB_PR004_V028_RoofBeam_")
    if superseded_crane or superseded_roof_grid:
        actor.set_actor_hidden_in_game(True)
        try:
            actor.set_is_temporarily_hidden_in_editor(True)
        except Exception:
            pass
        hidden.append({"label": label, "asset": asset})

if len(hidden) < 20:
    raise RuntimeError(f"fail closed: only {len(hidden)} legacy overhead actors matched")
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save cleaned candidate map")

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__INBOUND_LEGACY_OVERHEAD_HIDDEN",
    "candidate_map": MAP,
    "candidate_sha256": digest(MAP_FILE),
    "hidden_actor_count": len(hidden),
    "hidden_actors": hidden,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_INBOUND_CLEAN_PASS count={len(hidden)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
