"""Transient three-view proof of the player-built untouched AGV carrying its coil."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = ROOT / "Saved/ValidationScreenshots/PressShop/PlayerBuildable_v967/CoilAGV"
AUDIT = ROOT / "Saved/Audits/PressTrains/integrated_coil_agv_v967.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
VIEWS = (
    ("integrated_agv_hero.png", (420, -420, 265), (0, 0, 112), 43.0),
    ("integrated_agv_front.png", (455, 0, 145), (0, 0, 110), 41.0),
    ("integrated_agv_side.png", (0, -455, 145), (0, 0, 110), 41.0),
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 baseline drift before integrated AGV capture")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load clean validation substrate: {MAP}")

# Use the clean rebuild only as an unsaved world substrate.
for existing in actors.get_all_level_actors():
    existing.set_actor_hidden_in_game(True)
    existing.set_is_temporarily_hidden_in_editor(True)

agv = actors.spawn_actor_from_class(unreal.LBCoilAGVController, unreal.Vector(), unreal.Rotator())
if not agv or not agv.discover_and_bind():
    raise RuntimeError("Player-built untouched AGV failed to self-bind")
if not agv.configure_route(unreal.Vector(0, 0, 29), unreal.Vector(350, 0, 29),
                           unreal.Vector(350, 300, 29)):
    raise RuntimeError("Player-built untouched AGV failed to accept capture route")
agv.set_actor_label("LB_TRANSIENT_PlayerBuilt_CoilAGV_v967")
agv.set_actor_hidden_in_game(False)
agv.set_is_temporarily_hidden_in_editor(False)

cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -6), unreal.Rotator())
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(9, 9, 0.1))
floor.static_mesh_component.set_editor_properties({"visible": True, "hidden_in_game": False,
                                                   "cast_shadow": True})
floor.set_actor_hidden_in_game(False)
floor.set_is_temporarily_hidden_in_editor(False)

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator())
sky_cube = unreal.EditorAssetLibrary.load_asset("/Engine/EngineSky/DefaultTextureCube.DefaultTextureCube")
if sky_cube:
    sky.light_component.set_editor_properties({"source_type": unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP,
                                               "cubemap": sky_cube, "intensity": 0.42})
key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 400),
                                    unreal.Rotator(pitch=-48, yaw=-32, roll=0))
key.light_component.set_editor_properties({"intensity": 0.9, "cast_shadows": True})
for location, intensity, radius in [((-260, -220, 220), 650.0, 700.0),
                                    ((230, 210, 210), 500.0, 650.0)]:
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.light_component.set_editor_properties({"intensity": intensity,
                                                 "attenuation_radius": radius,
                                                 "cast_shadows": False})

pp = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
pp.set_editor_properties({"unbound": True, "blend_weight": 1.0})
settings = pp.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": -1.45,
    "override_bloom_intensity": True, "bloom_intensity": 0.0,
    "override_motion_blur_amount": True, "motion_blur_amount": 0.0,
})
pp.set_editor_property("settings", settings)
world = unreal.EditorLevelLibrary.get_editor_world()
for command in ("viewmode lit", "r.TextureStreaming 0", "r.Streaming.FullyLoadUsedTextures 1",
                "r.EyeAdaptationQuality 0", "r.DefaultFeature.AutoExposure 0",
                "r.DefaultFeature.Bloom 0", "r.DefaultFeature.MotionBlur 0", "r.ScreenPercentage 100"):
    unreal.SystemLibrary.execute_console_command(world, command)
unreal.EditorLevelLibrary.editor_set_game_view(True)

cameras = []
for _, location, target, fov in VIEWS:
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16 / 9,
                                                   "constrain_aspect_ratio": True,
                                                   "post_process_blend_weight": 1.0})
    cameras.append(camera)

OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.png"):
    old.unlink()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

index = 0
started = 0.0
handle = None
records = []


def begin_capture():
    global started
    output = OUT / VIEWS[index][0]
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=cameras[index],
                                                      mask_enabled=False, capture_hdr=False,
                                                      delay=0.9, force_game_view=True)
    started = time.monotonic()


def finish():
    protected_after = sha256(PROTECTED)
    passed = all(row["status"] == "CAPTURE_PASS" for row in records) and protected_after == PROTECTED_SHA
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_INTEGRATED_UNTOUCHED_COIL_AGV" if passed else "FAIL",
        "map_substrate": MAP, "map_saved_during_capture": False,
        "owned_presentation": agv.is_using_approved_player_built_presentation(),
        "vehicle_location_cm": list(agv.get_vehicle_location().to_tuple()),
        "load_bottom_datum_cm": 12.5, "body_visual_yaw_degrees": 90.0,
        "meshy_credits_used": 0, "captures": records,
        "protected_v438_sha256": protected_after,
    }, indent=2), encoding="utf-8")
    (unreal.log if passed else unreal.log_error)(
        "LINE_BOSS_INTEGRATED_COIL_AGV_V967_PASS" if passed else "LINE_BOSS_INTEGRATED_COIL_AGV_V967_FAIL")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_):
    global index, handle
    output = OUT / VIEWS[index][0]
    ready = output.exists() and output.stat().st_size > 4096
    if not ready and time.monotonic() - started < 120:
        return
    records.append({"file": str(output), "bytes": output.stat().st_size if output.exists() else 0,
                    "sha256": sha256(output) if ready else None,
                    "status": "CAPTURE_PASS" if ready else "CAPTURE_FAIL"})
    index += 1
    if index < len(VIEWS):
        begin_capture()
        return
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    finish()


begin_capture()
handle = unreal.register_slate_post_tick_callback(tick)
