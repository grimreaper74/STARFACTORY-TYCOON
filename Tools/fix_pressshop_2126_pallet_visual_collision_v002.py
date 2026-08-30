"""Force the three detailed hover-pallet cards to remain visual-only."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "pallet_visual_collision_v002_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected authority changed: " + str(path))
if OUT.exists():
    raise RuntimeError("refusing to overwrite pallet collision evidence")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
rows = []
for slot in ("A", "B", "C"):
    label = f"2126 OUTBOUND | detailed finished-panel hover pallet sprite {slot}"
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("detailed pallet card missing: " + label)
    component = actor.static_mesh_component
    before_state = str(component.get_collision_enabled())
    component.set_collision_profile_name("NoCollision")
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_generate_overlap_events(False)
    after_state = str(component.get_collision_enabled())
    if "NO_COLLISION" not in after_state.upper():
        raise RuntimeError("pallet card collision did not disable: " + label + " => " + after_state)
    rows.append({"label": label, "before": before_state, "after": after_state, "profile": str(component.get_collision_profile_name())})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("pallet visual collision correction did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during pallet collision correction")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__DETAILED_PALLET_CARDS_VISUAL_ONLY",
    "map": MAP,
    "cards": rows,
    "native_collision_bases_preserved": 3,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_PALLET_VISUAL_COLLISION_PASS receipt=" + str(OUT))
unreal.SystemLibrary.quit_editor()
