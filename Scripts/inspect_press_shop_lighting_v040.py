"""Read-only v040 light inventory for the factory luminaire rework."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_lighting_inventory_v040.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
rows = []
for actor in actors.get_all_level_actors():
    component = actor.get_component_by_class(unreal.LightComponent)
    if component is None:
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    try:
        radius = float(component.get_editor_property("attenuation_radius"))
    except Exception:
        radius = None
    rows.append({
        "label": actor.get_actor_label(), "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "rotation": [rotation.roll, rotation.pitch, rotation.yaw],
        "intensity": float(component.get_editor_property("intensity")),
        "attenuation_radius": radius,
        "cast_shadows": bool(component.get_editor_property("cast_shadows")),
        "tags": [str(tag) for tag in actor.tags],
    })
rows.sort(key=lambda row: row["label"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LIGHT_INVENTORY_V040_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
