"""Read-only spatial probe for candidate bounds and v303 camera corridors."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAModularMatchedCamerasCandidate_v303"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/press_train_a_v303_camera_corridors_v304.json"
CAMERA_LABELS = {
    "LB_V303_CAM_TrainAOperatorMatched",
    "LB_V303_CAM_TrainARearMatched",
    "LB_V303_CAM_TrainAElevatedMatched",
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

actors = actors_api.get_all_level_actors()
candidate = next(
    (a for a in actors if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}),
    None,
)
if candidate is None:
    raise RuntimeError("candidate missing")

origin, extent = candidate.get_actor_bounds(False)
candidate_bounds = {
    "label": candidate.get_actor_label(),
    "location": [candidate.get_actor_location().x, candidate.get_actor_location().y, candidate.get_actor_location().z],
    "origin": [origin.x, origin.y, origin.z],
    "extent": [extent.x, extent.y, extent.z],
    "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
    "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
}

cameras = []
for actor in actors:
    if actor.get_actor_label() in CAMERA_LABELS:
        loc = actor.get_actor_location()
        cameras.append({"label": actor.get_actor_label(), "location": [loc.x, loc.y, loc.z]})

# Capture nearby visible actors likely to block a side-on review corridor.
nearby = []
for actor in actors:
    if actor == candidate or actor.get_actor_label() in CAMERA_LABELS or actor.is_hidden_ed():
        continue
    try:
        o, e = actor.get_actor_bounds(False)
    except Exception:
        continue
    if e.x <= 1 and e.y <= 1 and e.z <= 1:
        continue
    if (candidate_bounds["min"][0] - 800 <= o.x <= candidate_bounds["max"][0] + 800 and
            candidate_bounds["min"][1] - 3000 <= o.y <= candidate_bounds["max"][1] + 3000):
        nearby.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "origin": [round(o.x, 2), round(o.y, 2), round(o.z, 2)],
            "extent": [round(e.x, 2), round(e.y, 2), round(e.z, 2)],
            "tags": [str(t) for t in actor.tags],
        })

payload = {
    "$schema": "cairnwell/audit/train-a-v303-camera-corridors/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "candidate": candidate_bounds,
    "cameras": sorted(cameras, key=lambda x: x["label"]),
    "nearby_visible_actor_count": len(nearby),
    "nearby_visible_actors": sorted(nearby, key=lambda x: (x["origin"][1], x["origin"][0], x["label"])),
    "read_only": True,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
