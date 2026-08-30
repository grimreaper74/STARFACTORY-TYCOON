"""What is actually lighting the spacecraft factory?

The ground was set to the spec's Ground.Prepared #C2BDB4 - saturation
8%, value 76% - and rendered back at saturation 14%, value 83%. A
rendered pixel is albedo times light, so it will never equal its
albedo; but neutral light preserves SATURATION roughly intact, and
ours nearly doubled it. That points at the light, not the surface.

It matters more than any single colour. A warm key pushes every
surface in the scene toward the amber arc at once, which is the exact
global failure the brand spec cites when it rules out a dusk setting:
"Dusk pushes every neutral warm-orange, which lands the whole world in
Machine.Amber's hue arc and breaks the saturation test globally."

Only ONE light colour exists anywhere in the C++ - a warm work lamp at
FColor(255, 247, 235). The key light is therefore in the map package,
where it is invisible to the release gate, untested, and free to drift.
This reads it before anything is changed.

Read-only: it opens the map, reports, and writes nothing.
"""
import unreal

MAPS = [
    "/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
    "/Maps/LB_SpacecraftFactory_v001",
]

# The actor classes that decide the look of a scene before any material
# is considered. A post-process volume is included because a colour
# grade there would explain a warm cast that no light accounts for.
OF_INTEREST = (
    "DirectionalLight", "SkyLight", "SkyAtmosphere", "PostProcessVolume",
    "ExponentialHeightFog", "AtmosphericFog", "PointLight", "SpotLight",
    "RectLight", "VolumetricCloud",
)


def describe_light(component):
    """Colour, intensity and temperature - the three that set the cast."""
    out = []
    for name in ("intensity", "light_color", "temperature",
                 "use_temperature", "indirect_lighting_intensity",
                 "volumetric_scattering_intensity"):
        try:
            out.append("%s=%s" % (name, component.get_editor_property(name)))
        except Exception:
            pass
    return "  ".join(out)


for map_path in MAPS:
    unreal.log("=" * 66)
    unreal.log("MAP %s" % map_path)
    unreal.log("=" * 66)
    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        unreal.log_warning("  MISSING - not an asset")
        continue
    unreal.EditorLoadingAndSavingUtils.load_map(map_path)

    actors = unreal.EditorActorSubsystem().get_all_level_actors()
    unreal.log("  %d actors in level" % len(actors))
    found = 0
    for actor in actors:
        class_name = actor.get_class().get_name()
        if not any(k in class_name for k in OF_INTEREST):
            continue
        found += 1
        unreal.log("  ---- %s  (%s)"
                   % (actor.get_actor_label(), class_name))
        unreal.log("       at %s  rot %s"
                   % (actor.get_actor_location(),
                      actor.get_actor_rotation()))
        for component in actor.get_components_by_class(
                unreal.LightComponentBase):
            unreal.log("       %s" % describe_light(component))
    if found == 0:
        unreal.log_warning(
            "  NO LIGHTS, SKY OR POST-PROCESS IN THIS MAP AT ALL - the "
            "look is coming from engine defaults, which is worse than a "
            "wrong light because there is nothing to point at.")
