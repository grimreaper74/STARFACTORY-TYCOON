"""List every light component saved in the OneFactory map.

The lamp pools survived three source-side edits, so find out which lights
actually exist in the level rather than guessing. Prints owner label,
class, tags, intensity, falloff mode and height for each light.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_level_lights.json"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

rows = []
for actor in ACTOR_SUB.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.LightComponentBase):
        row = {
            "actor": actor.get_actor_label(),
            "actor_class": actor.get_class().get_name(),
            "tags": [str(t) for t in actor.tags],
            "component_class": component.get_class().get_name(),
            "intensity": float(component.get_editor_property("intensity")),
            "z": round(actor.get_actor_location().z, 1),
        }
        if isinstance(component, unreal.PointLightComponent):
            row["attenuation"] = float(
                component.get_editor_property("attenuation_radius"))
            row["inverse_square"] = bool(
                component.get_editor_property("use_inverse_squared_falloff"))
        rows.append(row)

with open(OUT, "w") as handle:
    json.dump(rows, handle, indent=1)
unreal.log("LINE_BOSS_LIGHT_DUMP count={} out={}".format(len(rows), OUT))
