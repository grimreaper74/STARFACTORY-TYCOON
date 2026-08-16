"""Read-only Train A authority/collision inventory for a safe visual replacement plan."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
AUDIT_REL = "Audits/PressTrains/press_train_a_integration_authority_plan_v335.json"
TRAIN_TAG = "LB.PressTrain.Installed.TRAIN_A"
TRAIN_PREFIX = "LB_INST_PTA_"
AUTHORITY_WORDS = (
    "AUTHORITY", "RUNTIME", "CONTROLLER", "MANAGER", "MOVER", "RAM", "SLIDE",
    "DIE", "TRANSFER", "ROBOT", "HMI", "INTERLOCK", "SENSOR", "FAULT", "AUDIO",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def component_record(component: unreal.ActorComponent) -> dict:
    record = {
        "name": component.get_name(),
        "class": component.get_class().get_name(),
    }
    if isinstance(component, unreal.PrimitiveComponent):
        record.update({
            "visible": bool(component.is_visible()),
            "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            "collision_enabled": str(component.get_collision_enabled()),
            "generate_overlap_events": bool(component.get_editor_property("generate_overlap_events")),
            "mobility": str(component.mobility) if isinstance(component, unreal.SceneComponent) else None,
        })
    return record


def main() -> None:
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")

    records = []
    for actor in actors_api.get_all_level_actors():
        tags = sorted(str(tag) for tag in actor.tags)
        label = actor.get_actor_label()
        if TRAIN_TAG not in tags and not label.upper().startswith(TRAIN_PREFIX):
            continue
        components = [component_record(c) for c in actor.get_components_by_class(unreal.ActorComponent)]
        identity = " ".join([label, actor.get_class().get_name(), *tags]).upper()
        runtime_hint = any(word in identity for word in AUTHORITY_WORDS)
        collision_components = [c for c in components if c.get("collision_enabled") not in (None, "NoCollision")]
        records.append({
            "label": label,
            "name": actor.get_name(),
            "class": actor.get_class().get_name(),
            "tags": tags,
            "location_cm": list(actor.get_actor_location().to_tuple()),
            "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
            "scale": list(actor.get_actor_scale3d().to_tuple()),
            "runtime_authority_hint": runtime_hint,
            "collision_component_count": len(collision_components),
            "components": components,
        })

    records.sort(key=lambda item: item["label"])
    authority = [item for item in records if item["runtime_authority_hint"]]
    blockers = [item for item in records if item["collision_component_count"]]
    project = Path(unreal.Paths.project_dir())
    map_file = project / "Content/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301.umap"
    output = Path(unreal.Paths.project_saved_dir()) / AUDIT_REL
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "$schema": "cairnwell/audit/press-train-a-integration-authority-plan-v335/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READ_ONLY_INVENTORY__MANUAL_CLASSIFICATION_REQUIRED__NO_MAP_MUTATION",
        "map": MAP,
        "map_sha256": sha256(map_file),
        "train_actor_count": len(records),
        "runtime_authority_hint_count": len(authority),
        "collision_actor_count": len(blockers),
        "rules": [
            "Never delete or disable a runtime-authority actor merely to remove old visuals.",
            "Retain authoritative collision until replacement collision passes exact overlap/navigation gates.",
            "Hide only positively classified superseded presentation components in a fresh child map.",
            "The v040 aggregate mesh remains visual-only until modular collision and mover mapping pass.",
        ],
        "actors": records,
        "promotion_authorized": False,
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        f"LB_TRAIN_A_AUTHORITY_INVENTORY_PASS actors={len(records)} "
        f"authority_hints={len(authority)} collision_actors={len(blockers)} output={output}"
    )


if __name__ == "__main__":
    main()
