"""Report structural obstructions and bounds around the installed Train A comparison area."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAShellComparisonCandidate_v290"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_camera_obstructions_v290.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(MAP)

items = []
for actor in actors.get_all_level_actors():
    loc = actor.get_actor_location()
    label = actor.get_actor_label()
    cls = actor.get_class().get_name()
    # Keep every likely obstruction close enough to affect Train A camera rays.
    likely = (any(token in label.lower() for token in ("column", "pillar", "wall", "liner", "shell"))
              or isinstance(actor, (unreal.PointLight, unreal.RectLight, unreal.SpotLight)))
    near = 500 <= loc.x <= 9000 and -7000 <= loc.y <= -2500
    if likely and near:
        origin, extent = actor.get_actor_bounds(False, False)
        item = {
            "label": label,
            "class": cls,
            "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
            "bounds_origin_cm": [round(origin.x, 2), round(origin.y, 2), round(origin.z, 2)],
            "bounds_extent_cm": [round(extent.x, 2), round(extent.y, 2), round(extent.z, 2)],
            "tags": [str(t) for t in actor.tags],
        }
        light = actor.get_component_by_class(unreal.LightComponent)
        if light:
            item["light"] = {
                "intensity": light.get_editor_property("intensity"),
                "attenuation_radius": light.get_editor_property("attenuation_radius") if hasattr(light, "attenuation_radius") else None,
                "cast_shadows": light.get_editor_property("cast_shadows"),
            }
        items.append(item)

items.sort(key=lambda x: (x["location_cm"][0], x["location_cm"][1], x["label"]))
payload = {"map": MAP, "train_a_focus_cm": [3850, -4742, 500], "obstruction_count": len(items), "actors": items}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
