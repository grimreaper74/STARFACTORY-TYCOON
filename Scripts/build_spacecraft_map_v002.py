"""Build LB_SpacecraftFactory_v002 - a fresh map with a real lighting rig.

Owner call (2026-09-01): rather than fight v001's darkness asset by
asset, start a new map. Diagnosis behind it: EVERYTHING renders dark
inside the hall on v001 - old assets included - so the interior
lighting/exposure is the root cause, not the materials.

The map stays true to the premade-factory contract: it contains ONLY
world settings and light. Every building, station and drone still
arrives through the authorities at runtime.

Rig (clean futuristic industrial - bright, even, no moody shadows):
  - DirectionalLight, high angle, 8 lux, atmosphere sun
  - SkyLight, realtime capture, boosted - the even industrial fill
  - SkyAtmosphere so the capture has something to see
  - PostProcessVolume, unbound, exposure LOCKED (min=max EV100 1.0)
    so interiors do not auto-expose into murk
  - GameMode override: ALBSpacecraftGameMode
"""
import unreal

DEST_DIR = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v002/Maps"
MAP_NAME = "LB_SpacecraftFactory_v002"


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    map_path = "%s/%s" % (DEST_DIR, MAP_NAME)
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        unreal.log_error("MAP EXISTS: %s - refusing overwrite." % map_path)
        return
    if not les.new_level(map_path):
        unreal.log_error("MAP CREATE FAILED: %s" % map_path)
        return

    sun = eas.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 500),
        unreal.Rotator(-55.0, 35.0, 0.0))
    sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_comp.set_editor_property("intensity", 8.0)
    sun_comp.set_editor_property("atmosphere_sun_light", True)

    sky = eas.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 600), unreal.Rotator())
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_comp.set_editor_property(
        "source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
    sky_comp.set_editor_property("intensity", 3.0)
    sky_comp.set_editor_property("real_time_capture", True)

    eas.spawn_actor_from_class(
        unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator())

    ppv = eas.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
    ppv.set_editor_property("unbound", True)
    settings = ppv.get_editor_property("settings")
    settings.set_editor_property("override_auto_exposure_min_brightness", True)
    settings.set_editor_property("override_auto_exposure_max_brightness", True)
    settings.set_editor_property("auto_exposure_min_brightness", 1.0)
    settings.set_editor_property("auto_exposure_max_brightness", 1.0)
    ppv.set_editor_property("settings", settings)

    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    ws.set_editor_property(
        "default_game_mode",
        unreal.load_class(None,
            "/Script/LineBossCarFactory.LBSpacecraftGameMode"))

    if not les.save_current_level():
        unreal.log_error("MAP SAVE FAILED")
        return
    unreal.log("MAP BUILT: %s (sun 8lx, skylight 3, exposure locked)"
               % map_path)


main()
