"""Shadow-ratio fix for LB_SpacecraftFactory_v002 (audit 2026-09-01).

The v002 rig carried v001's proven values (sun 34 lx / sky 2.2, locked
exposure, bias -3.0) - proven for the OUTDOOR site, but 15.5:1
direct:ambient lit the indoor factory like a car park: hard navy shadow
bars dominated every frame and machine shadow sides crushed to black
(pixel-verified in Saved/Screenshots/WindowsEditor/v004_check.png).

Fix: keep the TOTAL lit level constant (36.2 -> 36.0) so the locked
exposure stays honest, and move a third of it into the ambient fill.
Sun 25 / sky 11 = 2.3:1. Settled by LIVE iteration through the VibeUE
MCP editor session on 2026-09-01: 27/9 was judged from a PIE capture as
better-but-still-heavy, 25/11 judged right; the values were applied and
the level saved in that session. This script is the reproducible lane
for the same change (rerun after any map rebuild).
"""
import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/LineBoss/Candidates/Spacecraft/"
               "SpacecraftFactory_v002/Maps/LB_SpacecraftFactory_v002")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for actor in eas.get_all_level_actors():
    cls = actor.get_class().get_name()
    if cls == "DirectionalLight":
        c = actor.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_editor_property("intensity", 25.0)
    elif cls == "SkyLight":
        c = actor.get_component_by_class(unreal.SkyLightComponent)
        c.set_editor_property("intensity", 11.0)
        c.recapture_sky()

if les.save_current_level():
    unreal.log("V003 SHADOW RATIO: sun 25 / sky 11 (2.3:1), total held")
else:
    unreal.log_error("SAVE FAILED")
