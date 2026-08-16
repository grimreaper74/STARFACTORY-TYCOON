"""Read-only audit of installed A-D centres/envelopes before any layout change."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/press_train_abcd_layout_envelopes_v346.json"
PREFIXES = {name: f"LB_INST_PT{name}_" for name in "ABCD"}
TAGS = {name: f"LB.PressTrain.Installed.TRAIN_{name}" for name in "ABCD"}
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {OUT}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

def union_bounds(actors):
    minimum = [float("inf")] * 3
    maximum = [float("-inf")] * 3
    used = 0
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        if extent.x == 0 and extent.y == 0 and extent.z == 0:
            continue
        used += 1
        for i, (o, e) in enumerate(zip(origin.to_tuple(), extent.to_tuple())):
            minimum[i] = min(minimum[i], o - e)
            maximum[i] = max(maximum[i], o + e)
    return {
        "bounded_actor_count": used,
        "min_cm": minimum,
        "max_cm": maximum,
        "centre_cm": [(a + b) / 2.0 for a, b in zip(minimum, maximum)],
        "size_cm": [b - a for a, b in zip(minimum, maximum)],
    }

all_actors = actors_api.get_all_level_actors()
trains = {}
for name in "ABCD":
    members = []
    for actor in all_actors:
        label = actor.get_actor_label().upper()
        tags = {str(tag) for tag in actor.tags}
        if label.startswith(PREFIXES[name]) or TAGS[name] in tags:
            members.append(actor)
    trains[name] = {"actor_count": len(members), "native_envelope": union_bounds(members)}
replacement = next((a for a in all_actors if a.get_actor_label() == "CA_MW_PTA_v040_RELEASE_VISUAL_SUBSTRATE_v343"), None)
if replacement is None:
    raise RuntimeError("v343 replacement missing")
trains["A"]["new_visible_envelope"] = union_bounds([replacement])
centres_y = {n: trains[n]["native_envelope"]["centre_cm"][1] for n in "ABCD"}
ordered = sorted(centres_y, key=centres_y.get)
adjacent = [{"train_1": a, "train_2": b, "centre_pitch_y_cm": centres_y[b] - centres_y[a]}
            for a, b in zip(ordered, ordered[1:])]
payload = {
    "$schema": "cairnwell/audit/press-train-abcd-layout-envelopes-v346/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_LAYOUT_AUDIT__NO_MAP_CHANGE__ALL_CLEARANCES_TBC",
    "map": MAP,
    "trains": trains,
    "ordered_by_y": ordered,
    "adjacent_centre_pitches": adjacent,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LB_TRAIN_ABCD_LAYOUT_V346_PASS {OUT}")
unreal.SystemLibrary.quit_editor()
