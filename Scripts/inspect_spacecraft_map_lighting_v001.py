"""inspect_spacecraft_map_lighting_v001.py - READ-ONLY. A rendered
capture of the spacecraft factory came out flat: uniform ambient with
no visible shadowing anywhere, even after cast-shadow was enabled on
the presenter's meshes. A shadow needs a light that casts one, so this
lists every light, sky and fog actor in the map and what it is set to.
"""

import unreal

MAP = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
       "/Maps/LB_SpacecraftFactory_v001")

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("MAPLIGHT actors=%d" % len(actors))
interesting = 0
for actor in actors:
    name = actor.get_class().get_name()
    if not any(k in name for k in ("Light", "Sky", "Fog", "Atmosphere",
                                   "PostProcess")):
        continue
    interesting += 1
    detail = ""
    comp = actor.get_component_by_class(unreal.LightComponent)
    if comp is not None:
        try:
            detail = " intensity=%s castShadows=%s mobility=%s" % (
                comp.get_editor_property("intensity"),
                comp.get_editor_property("cast_shadows"),
                comp.get_editor_property("mobility"))
        except Exception as exc:  # noqa: BLE001 - diagnostic lane
            detail = " (unreadable: %s)" % exc
    unreal.log("MAPLIGHT %s '%s'%s"
               % (name, actor.get_actor_label(), detail))
unreal.log("MAPLIGHT lighting-related actors=%d" % interesting)
unreal.log("MAPLIGHT DONE")
