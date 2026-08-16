"""Read-only inspection of v103 stack-ID placement and camera framing."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v103/stack_id_placement_inspection_v103.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
rows = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = {str(tag) for tag in actor.tags}
    is_stack = ("identified_blank_stack" in tags or "quality_hold_stack" in tags)
    if "V103_StackIDPlate" not in label and "V103_TEXT_StackID" not in label and label != "LB_PR010_V103_CAM_StackID" and not is_stack:
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    component = getattr(actor, "static_mesh_component", None)
    rows.append({
        "label": label,
        "tags": sorted(tags),
        "class": actor.get_class().get_name(),
        "location": [round(value, 3) for value in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "rotation": [round(value, 3) for value in (actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw)],
        "bounds_origin": [round(value, 3) for value in (origin.x, origin.y, origin.z)],
        "bounds_size": [round(value * 2, 3) for value in (extent.x, extent.y, extent.z)],
        "materials": [component.get_material(index).get_name() if component.get_material(index) else None for index in range(component.get_num_materials())] if component else [],
        "component_visible": bool(component.get_editor_property("visible")) if component else None,
        "component_hidden_in_game": bool(component.get_editor_property("hidden_in_game")) if component else None,
        "text": str(actor.text_render.get_editor_property("text")) if isinstance(actor, unreal.TextRenderActor) else None,
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
print(json.dumps({"map": MAP, "actors": rows}, indent=2))
