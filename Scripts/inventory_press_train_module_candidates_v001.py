"""Read-only actor inventory for retained Press Train A-D integration candidates."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/press_train_module_candidate_inventory_v001.json"
MAPS = {
    "A": "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027",
    "B": "/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001",
    "C": "/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001",
    "D": "/Game/LineBoss/Maps/LB_PressTrainDIsolatedVariantCandidate_v001",
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


payload = {
    "$schema": "cairnwell/audit/press-train-module-candidate-inventory-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_INVENTORY",
    "maps": {},
    "map_modified": False,
    "promotion_authorized": False,
}

for train, map_path in MAPS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(f"could not load retained map {map_path}")
    actors = list(actors_api.get_all_level_actors())
    rows = []
    for actor in actors:
        label = actor.get_actor_label()
        tags = [str(tag) for tag in actor.tags]
        rows.append({
            "label": label,
            "class": actor.get_class().get_name(),
            "location_cm": vec(actor.get_actor_location()),
            "rotation_deg": [
                round(float(actor.get_actor_rotation().pitch), 4),
                round(float(actor.get_actor_rotation().yaw), 4),
                round(float(actor.get_actor_rotation().roll), 4),
            ],
            "tags": tags,
            "validation_context_hint": any(
                token in label.lower()
                for token in ("camera", "cam_", "floor", "ceiling", "wall", "skylight", "postprocess", "directional")
            ) or any("validation" in tag.lower() for tag in tags),
        })
    payload["maps"][train] = {
        "map": map_path,
        "actor_count": len(rows),
        "class_counts": dict(sorted(Counter(row["class"] for row in rows).items())),
        "validation_context_hint_count": sum(row["validation_context_hint"] for row in rows),
        "actors": rows,
    }

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "status": payload["status"],
    "output": str(OUT),
    "maps": {
        key: {
            "actor_count": value["actor_count"],
            "class_counts": value["class_counts"],
            "validation_context_hint_count": value["validation_context_hint_count"],
        }
        for key, value in payload["maps"].items()
    },
}, indent=2))
unreal.SystemLibrary.quit_editor()
