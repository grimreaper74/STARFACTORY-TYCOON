"""Report the Moorcross map's existing lighting and exposure setup.

Adding a sun to a scene that was lit for interiors can blow out everything the
owner already tuned, so measure what is there before placing anything: which
light actors exist, whether a sky atmosphere and fog exist, and above all
whether any post-process volume pins exposure to a fixed value.
"""
import io
import json
import os

import unreal

OUT = os.environ.get("LB_LIGHT_OUT", "C:/Temp/lb_light.json")
LEVEL = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not LEVEL_SUB.load_level(LEVEL):
    raise RuntimeError("could not load {}".format(LEVEL))
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or LEVEL.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world open; use -ExecutePythonScript")

report = {"level": LEVEL, "actors": [], "lights": [], "post_process": []}

for actor in ACTOR_SUB.get_all_level_actors():
    if not actor:
        continue
    class_name = actor.get_class().get_name()
    report["actors"].append({
        "label": actor.get_actor_label(),
        "class": class_name,
        "tags": [str(t) for t in actor.tags],
    })

    if isinstance(actor, unreal.Light):
        component = actor.light_component
        entry = {"label": actor.get_actor_label(), "class": class_name}
        if component:
            for prop in ("intensity", "light_color", "cast_shadows",
                         "intensity_units", "temperature", "use_temperature"):
                try:
                    entry[prop] = str(component.get_editor_property(prop))
                except Exception:  # noqa: BLE001 - property varies by light type
                    pass
        entry["rotation"] = str(actor.get_actor_rotation())
        report["lights"].append(entry)

    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.get_editor_property("settings")
        pp = {"label": actor.get_actor_label(),
              "unbound": str(actor.get_editor_property("unbound")),
              "priority": str(actor.get_editor_property("priority"))}
        for flag, value in (
                ("override_auto_exposure_method", "auto_exposure_method"),
                ("override_auto_exposure_min_brightness", "auto_exposure_min_brightness"),
                ("override_auto_exposure_max_brightness", "auto_exposure_max_brightness"),
                ("override_auto_exposure_bias", "auto_exposure_bias"),
                ("override_bloom_intensity", "bloom_intensity")):
            try:
                if settings.get_editor_property(flag):
                    pp[value] = str(settings.get_editor_property(value))
            except Exception:  # noqa: BLE001 - settings differ across versions
                pass
        report["post_process"].append(pp)

interesting = ("DirectionalLight", "SkyLight", "SkyAtmosphere",
               "ExponentialHeightFog", "VolumetricCloud", "PostProcessVolume")
report["summary"] = {
    name: sum(1 for a in report["actors"] if a["class"] == name)
    for name in interesting
}
report["actor_total"] = len(report["actors"])
report["site_actor_total"] = sum(
    1 for a in report["actors"] if "LB.Site.Authored" in a["tags"])

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1))
unreal.log("LINE_BOSS_LIGHT_PROBE {} actors ({} site), summary {} -> {}".format(
    report["actor_total"], report["site_actor_total"], report["summary"], OUT))
