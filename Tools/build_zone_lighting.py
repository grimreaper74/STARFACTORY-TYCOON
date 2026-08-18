"""Light the new process zones the way the station rows already are.

The ED band, the marriage track gaps and the assembly test band carry saved
content that reads black at night exposure because only station rows have
lamp arches. Same verified recipe as build_gantry_lights: SM_LampArch01 at
1.6x with one 60,000 lumen shadowless SpotLight just under each apex.
Exposure is pinned at 1.0, so intensities are absolute.

Idempotent via LB.Zone.Lighting. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Zone.Lighting"
OUT = os.environ.get("LB_ZONE_LIGHT_OUT", "C:/Temp/lb_zone_lighting.json")
ARCH = "/Game/Meshes/SM_LampArch01"
SCALE = 1.6
HEIGHT = 880.0
INTENSITY = 60000.0
ATTENUATION = 3600.0
OUTER_CONE, INNER_CONE = 58.0, 24.0
TEMPERATURE = 4200.0

# (x, y) arch positions: ED band, marriage gaps, assembly test band.
POSITIONS = ([(1500.0 + n * 1900.0, -5300.0) for n in range(6)]
             + [(400.0, -5300.0), (12600.0, -5300.0)]
             + [(22200.0, 5500.0), (24800.0, 5500.0)]
             + [(5200.0, 12200.0), (7600.0, 12200.0), (20200.0, 12200.0)])

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"arches": 0, "lights": 0, "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

arch_mesh = unreal.load_asset(ARCH)
if arch_mesh is None:
    raise RuntimeError("missing arch mesh")

for x, y in POSITIONS:
    arch = ACTOR_SUB.spawn_actor_from_object(
        arch_mesh, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
    if arch is None:
        continue
    arch.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    arch.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                 unreal.Name("LB.NotProcessWIP")]
    arch.set_actor_label("Zone_LampArch")
    REPORT["arches"] += 1
    light = ACTOR_SUB.spawn_actor_from_class(
        unreal.SpotLight, unreal.Vector(x, y, HEIGHT),
        unreal.Rotator(-90.0, 0.0, 0.0))
    if light is None:
        continue
    component = light.light_component
    for name, value in (("intensity", INTENSITY),
                        ("intensity_units", unreal.LightUnits.LUMENS),
                        ("attenuation_radius", ATTENUATION),
                        ("outer_cone_angle", OUTER_CONE),
                        ("inner_cone_angle", INNER_CONE),
                        ("use_temperature", True),
                        ("temperature", TEMPERATURE),
                        ("cast_shadows", False)):
        component.set_editor_property(name, value)
    light.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    light.set_actor_label("Zone_LampArch_Light")
    REPORT["lights"] += 1

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_ZONE_LIGHTING {}".format(json.dumps(REPORT)))
