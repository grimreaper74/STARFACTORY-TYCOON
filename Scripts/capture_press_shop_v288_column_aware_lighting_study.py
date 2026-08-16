"""Capture an unsaved column-aware lighting study from protected v288.

This script never saves the level.  It spawns evidence-only cameras and point
lights in memory so their visual value can be judged before a successor map is
created.
"""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
CAPTURES = {
    "north": ((5000.0, 5550.0, 900.0), (5000.0, -1750.0, 390.0), 54.0),
    "south": ((5000.0, -5700.0, 820.0), (5000.0, -1550.0, 390.0), 54.0),
    "east": ((9600.0, 1450.0, 720.0), (4550.0, -1750.0, 360.0), 58.0),
    "train_a": ((7650.0, -5450.0, 560.0), (5200.0, -4300.0, 360.0), 52.0),
}

capture_id = os.environ.get("LB_V288_COLUMN_CAPTURE", "north").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"unknown capture id {capture_id}")

output = (
    Path(unreal.Paths.project_saved_dir())
    / "ValidationScreenshots/PressShopIntegration/v288_column_aware_lighting_study"
    / f"v288_study_{capture_id}.png"
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")

# Restrained, cool-neutral evidence fill over the installed trains.  These are
# deliberately unsaved and carry no engineering lux authority.
for row_id, y_value in enumerate((-4300.0, -2600.0, -900.0, 800.0), 1):
    for bay_id, x_value in enumerate((2500.0, 4500.0, 6500.0), 1):
        light = actors_api.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(x_value, y_value, 1500.0), unreal.Rotator()
        )
        if light is None:
            raise RuntimeError(f"could not spawn study light {row_id}:{bay_id}")
        light.set_actor_label(f"LB_V288_STUDY_HIGH_BAY_{row_id:02d}_{bay_id:02d}")
        component = light.point_light_component
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_properties({
            "intensity": 650.0,
            "attenuation_radius": 1450.0,
            "source_radius": 45.0,
            "light_color": unreal.Color(205, 218, 228, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name("LB.EvidenceOnly.Unsaved"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
        ]

location, target, fov = CAPTURES[capture_id]
camera = actors_api.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(*location), unreal.Rotator()
)
if camera is None:
    raise RuntimeError("could not spawn study camera")
camera.set_actor_label(f"LB_V288_STUDY_CAM_{capture_id.upper()}")
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)),
    False,
)
camera.camera_component.set_editor_properties({
    "field_of_view": fov,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})
camera.tags = [unreal.Name("LB.EvidenceOnly.Unsaved"), unreal.Name("LB.Camera.ColumnAwareStudy")]

output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(output),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell Moorcross protected v288 unsaved column-aware study {capture_id}",
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")

started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_V288_COLUMN_STUDY_PASS id={capture_id} path={output}")
    elif elapsed < 65.0:
        return
    else:
        unreal.log_error(f"LB_V288_COLUMN_STUDY_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


handle = unreal.register_slate_post_tick_callback(finish)
