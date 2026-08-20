"""Calm the saved shop spotlights to a lights-out wash.

The level carries 63 SpotLights at 60,000 cd (inverse-square) from an
earlier per-shop lighting pass - the 'light pools' the owner rejected:
Moorcross is a lights-out plant, robots inspect by machine vision, so a
fixture should read only slightly brighter than the shop around it
(owner, 2026-08-20). Every saved spotlight above the threshold becomes a
weak, flat-falloff wash; everything else is left alone.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_fix_lights.json"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

report = {"calmed": [], "untouched": 0}
for actor in ACTOR_SUB.get_all_level_actors():
    for component in actor.get_components_by_class(
            unreal.SpotLightComponent):
        intensity = float(component.get_editor_property("intensity"))
        if intensity < 10000.0:
            report["untouched"] += 1
            continue
        component.set_editor_property("use_inverse_squared_falloff", False)
        component.set_editor_property("light_falloff_exponent", 1.5)
        component.set_editor_property("intensity", 3.5)
        report["calmed"].append(actor.get_actor_label())

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(report, handle, indent=1)
unreal.log("LINE_BOSS_FIX_LIGHTS calmed={} untouched={}".format(
    len(report["calmed"]), report["untouched"]))
