"""Dump LB_SpacecraftFactory_v001's lighting rig to JSON (read-only)."""
import json
import unreal

OUT = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "Saved/Audits/Spacecraft/v001_lighting_dump.json")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/LineBoss/Candidates/Spacecraft/"
               "SpacecraftFactory_v001/Maps/LB_SpacecraftFactory_v001")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = []
for actor in eas.get_all_level_actors():
    cls = actor.get_class().get_name()
    if cls in ("DirectionalLight", "SkyLight", "PostProcessVolume",
               "SkyAtmosphere", "ExponentialHeightFog", "PointLight",
               "RectLight", "SpotLight"):
        entry = {"class": cls, "name": actor.get_actor_label(),
                 "rotation": str(actor.get_actor_rotation())}
        if cls == "DirectionalLight":
            c = actor.get_component_by_class(
                unreal.DirectionalLightComponent)
            entry["intensity"] = c.get_editor_property("intensity")
            entry["color"] = str(c.get_editor_property("light_color"))
        if cls == "SkyLight":
            c = actor.get_component_by_class(unreal.SkyLightComponent)
            entry["intensity"] = c.get_editor_property("intensity")
            entry["source"] = str(c.get_editor_property("source_type"))
            entry["realtime"] = c.get_editor_property("real_time_capture")
        if cls == "PostProcessVolume":
            s = actor.get_editor_property("settings")
            entry["unbound"] = actor.get_editor_property("unbound")
            for prop in ("override_auto_exposure_min_brightness",
                         "override_auto_exposure_max_brightness",
                         "auto_exposure_min_brightness",
                         "auto_exposure_max_brightness",
                         "override_auto_exposure_bias",
                         "auto_exposure_bias"):
                try:
                    entry[prop] = s.get_editor_property(prop)
                except Exception:
                    pass
        report.append(entry)
with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=1, default=str)
unreal.log("LIGHT DUMP: %d actors -> %s" % (len(report), OUT))
