"""Read-only audit of PR-004 HMI component and physical presentation state."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_hmi_visual_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

station = next((actor for actor in actors.get_all_level_actors()
                if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation"), None)
if station is None:
    raise RuntimeError("Missing PR-004 station")

text_rows = []
for component in station.get_components_by_class(unreal.TextRenderComponent):
    if component.get_name().startswith("PR004_HMI_"):
        text_rows.append({
            "name": component.get_name(),
            "text": str(component.get_editor_property("text")),
            "location_cm": [component.get_world_location().x, component.get_world_location().y, component.get_world_location().z],
            "rotation_deg": [component.get_world_rotation().roll, component.get_world_rotation().pitch, component.get_world_rotation().yaw],
            "world_size_cm": component.get_editor_property("world_size"),
            "visible": component.is_visible(),
            "hidden_in_game": component.get_editor_property("hidden_in_game"),
        })

actor_rows = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith("LB_PR004_V026_HMI_"):
        actor_rows.append({
            "label": actor.get_actor_label(),
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
            "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
            "hidden": actor.get_editor_property("is_editor_only_actor"),
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-hmi-visual-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "station_location_cm": [station.get_actor_location().x, station.get_actor_location().y, station.get_actor_location().z],
    "text_components": sorted(text_rows, key=lambda row: row["name"]),
    "physical_actors": sorted(actor_rows, key=lambda row: row["label"]),
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_HMI_VISUAL_AUDIT_PASS output={OUT} text={len(text_rows)} actors={len(actor_rows)}")
