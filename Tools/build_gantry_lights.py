"""Put real light in the gantry arches.

The 50 SM_LampArch01 arches across weld, paint and assembly are mesh-only: their lamp
heads are emissive, so they LOOK lit but illuminate nothing. This adds one SpotLight per
arch, aimed down at the line beneath it.

Two constraints particular to this map:

* Exposure is PINNED. LB_OF_ENV_FixedExposureAuthority_v001 fixes auto-exposure min and
  max at 1.0, so the camera never adapts and every intensity is absolute. Values here
  are chosen against the existing 800,000 lumen overhead RectLight rather than by eye.
* Shadows off, deliberately. 50 shadow-casting spots across three shops is a large cost
  for little gain: high-bay lighting reads through the pool it lays on the floor, not
  through the shadows it casts.

Arch positions mirror the three placement scripts. Idempotent.
Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Gantry.Light"
OUT = os.environ.get("LB_GLIGHT_OUT", "C:/Temp/lb_glight.json")

INTENSITY = float(os.environ.get("LB_GANTRY_LUMENS", 60000.0))
HEIGHT = 880.0          # just under the 941 cm apex of a 1.6x arch
OUTER_CONE = 58.0
INNER_CONE = 24.0
ATTENUATION = 3600.0
TEMPERATURE = 4200.0

WELD = [(-3050.0 - n * 2000.0, -7000.0) for n in range(9)]
WELD += [(-19050.0 + n * 2000.0, -11200.0) for n in range(9)]
ASSEMBLY = [(4000.0 + n * 2200.0, 5500.0) for n in range(12)]
ASSEMBLY += [(28200.0 - n * 2200.0, 11500.0) for n in range(12)]
PAINT = [(x, -8500.0) for x in
         (0.0, 1700.0, 3400.0, 4800.0, 6600.0, 8800.0, 10500.0, 11800.0)]
ARCHES = [("Weld", WELD), ("Assembly", ASSEMBLY), ("Paint", PAINT)]

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"placed": {}, "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        REPORT["cleared"] += 1

for shop, positions in ARCHES:
    for index, (x, y) in enumerate(positions):
        light = ACTOR_SUB.spawn_actor_from_class(
            unreal.SpotLight, unreal.Vector(x, y, HEIGHT),
            unreal.Rotator(0.0, -90.0, 0.0))
        if light is None:
            continue
        c = light.light_component
        for name, value in (("intensity", INTENSITY),
                            ("intensity_units", unreal.LightUnits.LUMENS),
                            ("attenuation_radius", ATTENUATION),
                            ("outer_cone_angle", OUTER_CONE),
                            ("inner_cone_angle", INNER_CONE),
                            ("use_temperature", True),
                            ("temperature", TEMPERATURE),
                            ("cast_shadows", False)):
            try:
                c.set_editor_property(name, value)
            except Exception:  # noqa: BLE001 - property set varies by version
                pass
        # Aim straight down; spawning from a Rotator can land pitch in roll.
        light.set_actor_rotation(unreal.Rotator(0.0, -90.0, 0.0), False)
        light.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                      unreal.Name("LB.NotProcessWIP")]
        light.set_actor_label("{}_GantryLight_{:02d}".format(shop, index + 1))
        REPORT["placed"][shop] = REPORT["placed"].get(shop, 0) + 1

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_GANTRY_LIGHTS {}".format(json.dumps(REPORT)))
