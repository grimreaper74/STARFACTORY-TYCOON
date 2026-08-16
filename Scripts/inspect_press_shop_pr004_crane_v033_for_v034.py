"""Read-only actor/layout inventory used to author isolated crane candidate v034."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_v033_for_v034_inventory.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def vec(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


def rot(value):
    return [round(float(value.roll), 3), round(float(value.pitch), 3), round(float(value.yaw), 3)]


rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    interesting = (
        "30T" in label or "40T" in label or "Crane" in label
        or label.startswith("LB_COIL_LABEL_V026_")
        or label.startswith("LB_COIL_TEXT_V026_")
        or label.startswith("LB_INT_FRONT_FactoryFill_")
        or label.startswith("LB_PR004_V033_CAM_")
        or "LB.CoilSlot.CS-10.Attachment" in tags
    )
    if not interesting:
        continue
    row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": vec(actor.get_actor_location()),
        "rotation_deg": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "tags": tags,
        "hidden_in_game": bool(actor.get_editor_property("hidden")),
    }
    light = actor.get_component_by_class(unreal.LightComponent)
    if light is not None:
        row["light"] = {
            "intensity": float(light.get_editor_property("intensity")),
            "color": str(light.get_editor_property("light_color")),
        }
    camera = actor.get_component_by_class(unreal.CameraComponent)
    if camera is not None:
        row["camera"] = {
            "fov": float(camera.get_editor_property("field_of_view")),
        }
    rows.append(row)

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-v033-for-v034-inventory/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_INVENTORY_PASS",
    "map": MAP,
    "actor_count": len(rows),
    "actors": sorted(rows, key=lambda row: row["label"]),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_V033_FOR_V034_INVENTORY_PASS actors={len(rows)} output={OUT}")
unreal.SystemLibrary.quit_editor()
