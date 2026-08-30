"""Restage the three 2126 outbound hover pallets and rebase Sequencer keys.

The visual cards are attached to each collision base, so they follow the base
automatically. The five native moving actors per pallet are moved together and
their absolute Location.X defaults/keys are shifted by the same delta.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
SEQUENCE_PATH = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sequences/LS_CA_MW_2126_PressShopAutomationLoop_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "outbound_convoy_restage_v002_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap":
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap":
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
TARGET_BASE_X = {"A": 3900.0, "B": 4750.0, "C": 5600.0}
EXPECTED_BASE_X = {"A": 3450.0, "B": 5050.0, "C": 6650.0}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def group_labels(slot):
    return (
        f"2126 OUTBOUND | hover pallet {slot} collision base",
        f"2126 OUTBOUND | hover pallet {slot} safety rail north",
        f"2126 OUTBOUND | hover pallet {slot} safety rail south",
        f"2126 OUTBOUND | hover pallet {slot} status beacon",
        f"2126 OUTBOUND | finished-panel payload {slot}",
    )


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected authority missing or changed: " + str(path))
if RECEIPT.exists():
    raise RuntimeError("outbound restage receipt already exists; refusing overwrite")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
sequence = unreal.load_asset(SEQUENCE_PATH)
if not isinstance(sequence, unreal.LevelSequence):
    raise RuntimeError("native automation Level Sequence is missing")

bindings = {str(binding.get_display_name()): binding for binding in sequence.get_bindings()}
actor_moves = []
sequence_changes = []

for slot in ("A", "B", "C"):
    base_label = f"2126 OUTBOUND | hover pallet {slot} collision base"
    base = by_label.get(base_label)
    if base is None:
        raise RuntimeError("outbound base missing: " + base_label)
    base_x = float(base.get_actor_location().x)
    if abs(base_x - EXPECTED_BASE_X[slot]) > 1.0:
        raise RuntimeError(
            f"outbound base {slot} moved unexpectedly: {base_x} vs {EXPECTED_BASE_X[slot]}")
    delta = TARGET_BASE_X[slot] - base_x

    for label in group_labels(slot):
        actor = by_label.get(label)
        if actor is None:
            raise RuntimeError("outbound convoy actor missing: " + label)
        old_location = actor.get_actor_location()
        new_location = unreal.Vector(old_location.x + delta, old_location.y, old_location.z)
        if not actor.set_actor_location(new_location, False, False):
            raise RuntimeError("could not restage outbound actor: " + label)
        actor_moves.append({
            "slot": slot,
            "actor": label,
            "delta_x_cm": delta,
            "before_cm": [float(old_location.x), float(old_location.y), float(old_location.z)],
            "after_cm": [float(new_location.x), float(new_location.y), float(new_location.z)],
        })

        binding = bindings.get(label)
        if binding is None:
            raise RuntimeError("Sequencer binding missing for outbound actor: " + label)
        location_x_channels = []
        for track in binding.get_tracks():
            for section in track.get_sections():
                for channel in section.get_channels_by_type(unreal.MovieSceneScriptingDoubleChannel):
                    if str(channel.channel_name) == "Location.X":
                        location_x_channels.append(channel)
        if len(location_x_channels) != 1:
            raise RuntimeError(
                f"expected one Location.X channel for {label}, found {len(location_x_channels)}")
        channel = location_x_channels[0]
        default_before = float(channel.get_default()) if channel.has_default() else None
        if default_before is None:
            raise RuntimeError("Location.X channel has no default: " + label)
        channel.set_default(default_before + delta)
        keys_before = [float(key.get_value()) for key in channel.get_keys()]
        if len(keys_before) != 6:
            raise RuntimeError(f"expected six Location.X keys for {label}, found {len(keys_before)}")
        for key in channel.get_keys():
            key.set_value(float(key.get_value()) + delta)
        keys_after = [float(key.get_value()) for key in channel.get_keys()]
        for old_value, new_value in zip(keys_before, keys_after):
            if abs((new_value - old_value) - delta) > 0.01:
                raise RuntimeError("Sequencer key rebase failed: " + label)
        sequence_changes.append({
            "actor": label,
            "delta_x_cm": delta,
            "default_before": default_before,
            "default_after": float(channel.get_default()),
            "keys_before": keys_before,
            "keys_after": keys_after,
        })

# The detailed visible card must remain attached to each moved base and must
# stay visual-only; its world position follows the base automatically.
cards = []
for slot in ("A", "B", "C"):
    card_label = f"2126 OUTBOUND | detailed finished-panel hover pallet sprite {slot}"
    base_label = f"2126 OUTBOUND | hover pallet {slot} collision base"
    card = by_label.get(card_label)
    base = by_label.get(base_label)
    if not isinstance(card, unreal.StaticMeshActor) or base is None:
        raise RuntimeError("detailed card/base missing after outbound restage: " + slot)
    parent = card.get_attach_parent_actor()
    if parent != base:
        raise RuntimeError("detailed pallet card lost its base attachment: " + slot)
    if "NO_COLLISION" not in str(card.static_mesh_component.get_collision_enabled()).upper():
        raise RuntimeError("detailed pallet card is not visual-only: " + slot)
    loc = card.get_actor_location()
    cards.append({
        "slot": slot,
        "actor": card_label,
        "parent": parent.get_actor_label(),
        "world_location_cm": [float(loc.x), float(loc.y), float(loc.z)],
    })

unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False)
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("candidate map did not save after outbound restage")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during outbound restage")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__OUTBOUND_HOVER_PALLETS_RESTAGED_AND_SEQUENCE_REBASED",
    "map": MAP,
    "sequence": sequence.get_path_name(),
    "target_base_locations_cm": {
        slot: [TARGET_BASE_X[slot], 4495.0, 38.0] for slot in ("A", "B", "C")
    },
    "centre_spacing_cm": 850.0,
    "animated_actor_count": len(actor_moves),
    "actor_moves": actor_moves,
    "sequence_changes": sequence_changes,
    "attached_visual_cards": cards,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_RESTAGE_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
