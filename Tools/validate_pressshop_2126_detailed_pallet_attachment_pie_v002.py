"""PIE proof for detailed hover-pallet visuals on native animated bases."""
import hashlib
import json
import math
from pathlib import Path
import time
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "detailed_pallet_attachment_pie_v002.json"
SLOTS = ("A", "B", "C")
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def xyz(vector):
    return [vector.x, vector.y, vector.z]


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def take_sample(world):
    actors = {actor.get_actor_label(): actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)}
    rows = {}
    for slot in SLOTS:
        base_label = f"2126 OUTBOUND | hover pallet {slot} collision base"
        card_label = f"2126 OUTBOUND | detailed finished-panel hover pallet sprite {slot}"
        base = actors.get(base_label)
        card = actors.get(card_label)
        if base is None or card is None:
            raise RuntimeError(f"PIE pallet pair missing for slot {slot}")
        base_location = xyz(base.get_actor_location())
        card_location = xyz(card.get_actor_location())
        rows[slot] = {
            "base_location_cm": base_location,
            "card_location_cm": card_location,
            "card_minus_base_cm": [card_location[index] - base_location[index] for index in range(3)],
            "card_attach_parent_label": card.get_attach_parent_actor().get_actor_label() if card.get_attach_parent_actor() else None,
        }
    return rows


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if OUT.exists():
    raise RuntimeError("refusing to overwrite detailed-pallet PIE evidence")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")

level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
worlds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
samples = []
started = time.monotonic()
pie_started = None
handle = None
ended = False
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
level_editor.editor_play_simulate()


def finish(status, **extra):
    global handle, ended
    if not ended:
        try:
            level_editor.editor_request_end_play()
        except Exception:
            pass
        ended = True
    after = {str(path): digest(path) for path in PROTECTED}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "status": status,
        "map": MAP,
        "samples": samples,
        "protected_sha256_before": before,
        "protected_sha256_after": after,
        **extra,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global pie_started
    try:
        now = time.monotonic()
        world = worlds.get_game_world()
        if world is None:
            if now - started > 40.0:
                finish("FAIL_PIE_WORLD_TIMEOUT")
            return
        if pie_started is None:
            pie_started = now
        elapsed = now - pie_started
        thresholds = (0.50, 2.60, 4.80)
        if len(samples) < len(thresholds) and elapsed >= thresholds[len(samples)]:
            samples.append({"elapsed_seconds": round(elapsed, 3), "pallets": take_sample(world)})
        if len(samples) == 3:
            first = samples[0]["pallets"]
            max_base_motion = 0.0
            max_relative_drift = 0.0
            bad_parents = []
            for sample in samples:
                for slot in SLOTS:
                    row = sample["pallets"][slot]
                    expected_parent = f"2126 OUTBOUND | hover pallet {slot} collision base"
                    if row["card_attach_parent_label"] != expected_parent:
                        bad_parents.append({"slot": slot, "actual": row["card_attach_parent_label"]})
                    max_relative_drift = max(max_relative_drift, distance(
                        row["card_minus_base_cm"], first[slot]["card_minus_base_cm"]))
            for sample in samples[1:]:
                for slot in SLOTS:
                    max_base_motion = max(max_base_motion, distance(
                        sample["pallets"][slot]["base_location_cm"], first[slot]["base_location_cm"]))
            metrics = {
                "max_base_motion_cm": max_base_motion,
                "max_card_to_base_relative_drift_cm": max_relative_drift,
                "bad_parent_count": len(bad_parents),
            }
            if bad_parents:
                finish("FAIL_CARD_PARENT_CONTRACT", metrics=metrics, bad_parents=bad_parents)
            elif max_base_motion <= 100.0:
                finish("FAIL_NATIVE_BASES_DID_NOT_MOVE", metrics=metrics)
            elif max_relative_drift > 0.05:
                finish("FAIL_DETAILED_VISUAL_DRIFTED_FROM_BASE", metrics=metrics)
            elif {str(path): digest(path) for path in PROTECTED} != before:
                finish("FAIL_PROTECTED_MAP_CHANGED", metrics=metrics)
            else:
                finish("PASS__DETAILED_PALLET_VISUALS_FOLLOW_NATIVE_MOVERS", metrics=metrics,
                       runtime_seconds_observed=round(elapsed, 3), pallet_count=len(SLOTS))
        elif now - started > 70.0:
            finish("FAIL_PIE_ATTACHMENT_TIMEOUT")
    except Exception as exc:
        finish("FAIL_PIE_ATTACHMENT_EXCEPTION", error=repr(exc))


handle = unreal.register_slate_post_tick_callback(tick)
