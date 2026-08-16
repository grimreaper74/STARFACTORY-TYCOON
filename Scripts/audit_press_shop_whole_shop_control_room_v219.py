"""Read-only actor audit for the v219 whole-shop automation preview."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_WholeShopAutomationPreviewCandidate_v219"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_whole_shop_control_room_audit_v219.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = actors_api.get_all_level_actors()


def vector_list(value):
    return [float(value.x), float(value.y), float(value.z)]


classes = {}
for actor in actors:
    name = actor.get_class().get_name()
    classes[name] = classes.get(name, 0) + 1

stations = []
for actor in actors:
    if actor.get_class().get_name() != "LBPressTrainAStation":
        continue
    tags = sorted(str(tag) for tag in actor.tags)
    stations.append({
        "label": actor.get_actor_label(),
        "location_cm": vector_list(actor.get_actor_location()),
        "tags": tags,
    })

consoles = []
for actor in actors:
    if actor.get_class().get_name() == "LBControlRoomOperationsConsole":
        consoles.append({
            "label": actor.get_actor_label(),
            "location_cm": vector_list(actor.get_actor_location()),
            "tags": sorted(str(tag) for tag in actor.tags),
        })

scope_counts = {}
for suffix in ("TRAIN_A", "TRAIN_B", "TRAIN_C", "TRAIN_D"):
    scope = f"LB.PressTrain.Installed.{suffix}"
    scope_counts[scope] = sum(scope in [str(tag) for tag in actor.tags] for actor in actors)

result = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "read_only": True,
    "actor_count": len(actors),
    "class_counts": classes,
    "press_train_station_count": len(stations),
    "press_train_stations": stations,
    "control_room_operations_console_count": len(consoles),
    "control_room_operations_consoles": consoles,
    "installed_scope_counts": scope_counts,
    "status": "PASS" if len(stations) == 4 and len(consoles) >= 1 else "HOLD",
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LB_V219_CONTROL_AUDIT::{json.dumps(result)}")
