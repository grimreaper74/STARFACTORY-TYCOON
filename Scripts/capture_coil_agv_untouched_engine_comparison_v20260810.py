"""Transient neutral Unreal captures of the untouched Blender/Unity AGV proof."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
DEST = "/Game/LineBoss/Developer/Validation/EngineComparison/CoilAGV_Untouched_v20260810"
MESH_PATH = f"{DEST}/SM_Cairnwell_CoilAGV_Untouched_v20260810"
PBR_PATH = f"{DEST}/Materials/M_Cairnwell_CoilAGV_Untouched_PBR_v20260810"
BASE_PATH = f"{DEST}/Materials/M_Cairnwell_CoilAGV_Untouched_BaseColor_v20260810"
CONTROLLED_PATH = f"{DEST}/Materials/M_Cairnwell_CoilAGV_ControlledPaint_v20260810"
OUT = ROOT / "Saved/ValidationScreenshots/EngineComparison/CoilAGV/Unreal_Untouched_v20260810"
AUDIT = ROOT / "Saved/Audits/EngineComparison/coil_agv_unreal_untouched_capture_v20260810.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
EXPECTED_TRIANGLES = 1_984_003
CAPTURES = [
    ("01_unreal_controlled_lit.png", "controlled", (285, -360, 185), (0, 0, 35), 42.0),
    ("02_unreal_controlled_front.png", "controlled", (0, -420, 85), (0, 0, 32), 40.0),
    ("03_unreal_controlled_top.png", "controlled", (0, 0, 470), (0, 0, 20), 39.0),
    ("04_unreal_base_color.png", "base", (285, -360, 185), (0, 0, 35), 42.0),
    ("05_unreal_meshy_pbr_diagnostic.png", "pbr", (285, -360, 185), (0, 0, 35), 42.0),
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 baseline drift before AGV capture")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load clean validation substrate: {MAP}")
mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
pbr = unreal.EditorAssetLibrary.load_asset(PBR_PATH)
base_material = unreal.EditorAssetLibrary.load_asset(BASE_PATH)
controlled_material = unreal.EditorAssetLibrary.load_asset(CONTROLLED_PATH)
if not isinstance(mesh, unreal.StaticMesh) or not pbr or not base_material or not controlled_material:
    raise RuntimeError("Untouched AGV comparison assets are missing")
if mesh.get_num_triangles(0) != EXPECTED_TRIANGLES or mesh.get_num_lods() != 1:
    raise RuntimeError("Untouched AGV topology gate failed before capture")

# The factory map is only a safe world substrate; old content is never shown or saved.
for existing in actors.get_all_level_actors():
    existing.set_actor_hidden_in_game(True)
    existing.set_is_temporarily_hidden_in_editor(True)
world = unreal.EditorLevelLibrary.get_editor_world()
OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.png"):
    old.unlink()

target = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
target.set_actor_label("LB_TRANSIENT_CoilAGV_Untouched_v20260810")
target.static_mesh_component.set_static_mesh(mesh)
target.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
target.static_mesh_component.set_editor_properties({"visible": True, "hidden_in_game": False, "cast_shadow": True})
bounds = mesh.get_bounds()
target.set_actor_location(unreal.Vector(-bounds.origin.x, -bounds.origin.y,
                                        -bounds.origin.z + bounds.box_extent.z), False, False)
target.set_actor_hidden_in_game(False)
target.set_is_temporarily_hidden_in_editor(False)

cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -6), unreal.Rotator())
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(12, 12, 0.1))
floor.static_mesh_component.set_editor_properties({"visible": True, "hidden_in_game": False, "cast_shadow": True})
floor.set_actor_hidden_in_game(False)
floor.set_is_temporarily_hidden_in_editor(False)

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator())
sky_cube = unreal.EditorAssetLibrary.load_asset("/Engine/EngineSky/DefaultTextureCube.DefaultTextureCube")
if sky_cube:
    sky.light_component.set_editor_properties({"source_type": unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP,
                                               "cubemap": sky_cube, "intensity": 0.35})
key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 400),
                                    unreal.Rotator(pitch=-48, yaw=-32, roll=0))
key.light_component.set_editor_properties({"intensity": 0.8, "cast_shadows": True})
for label, location, intensity, radius in [
    ("Fill", (-240, -210, 175), 550.0, 650.0),
    ("Rim", (210, 180, 155), 400.0, 600.0),
]:
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(f"LB_TRANSIENT_{label}Light_v20260810")
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
    "override_auto_exposure_bias": True, "auto_exposure_bias": -1.6,
    "override_bloom_intensity": True, "bloom_intensity": 0.0,
    "override_motion_blur_amount": True, "motion_blur_amount": 0.0,
})
pp.set_editor_property("settings", settings)
for command in ["viewmode lit", "r.TextureStreaming 0", "r.Streaming.FullyLoadUsedTextures 1",
                "r.EyeAdaptationQuality 0", "r.DefaultFeature.AutoExposure 0",
                "r.DefaultFeature.Bloom 0", "r.DefaultFeature.MotionBlur 0", "r.ScreenPercentage 100"]:
    unreal.SystemLibrary.execute_console_command(world, command)
unreal.EditorLevelLibrary.editor_set_game_view(True)

cameras = []
for index, (_, _, location, look_at, fov) in enumerate(CAPTURES):
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(*look_at)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16 / 9,
                                                   "constrain_aspect_ratio": True,
                                                   "post_process_blend_weight": 1.0})
    cameras.append(camera)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

index = 0
started = 0.0
handle = None
records = []


def begin_capture():
    global started
    filename, material_mode, _, _, _ = CAPTURES[index]
    capture_material = {"pbr": pbr, "base": base_material, "controlled": controlled_material}[material_mode]
    target.static_mesh_component.set_material(0, capture_material)
    path = OUT / filename
    if path.exists():
        path.unlink()
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, str(path), camera=cameras[index],
                                                      mask_enabled=False, capture_hdr=False,
                                                      delay=0.75, force_game_view=True)
    started = time.monotonic()


def finish():
    protected_after = sha256(PROTECTED)
    passed = all(row["status"] == "CAPTURE_PASS" for row in records) and protected_after == PROTECTED_SHA
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_UNTOUCHED_AGV_UNREAL_NEUTRAL_CAPTURES" if passed else "FAIL",
        "map_substrate": MAP, "map_saved_during_capture": False,
        "mesh": MESH_PATH, "triangles_lod0": mesh.get_num_triangles(0), "lod_count": mesh.get_num_lods(),
        "actor_scale": list(target.get_actor_scale3d().to_tuple()),
        "asset_bounds_cm": list((mesh.get_bounds().box_extent * 2).to_tuple()),
        "lighting": "transient neutral key/fill/rim plus specified engine cubemap",
        "fixed_exposure_bias": -1.6, "captures": records,
        "protected_v438_sha256": protected_after, "meshy_credits_used": 0,
    }, indent=2), encoding="utf-8")
    unreal.log("LINE_BOSS_UNTOUCHED_AGV_UNREAL_CAPTURE_V20260810_PASS" if passed
               else "LINE_BOSS_UNTOUCHED_AGV_UNREAL_CAPTURE_V20260810_FAIL")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_):
    global index, handle
    filename, material_mode, _, _, _ = CAPTURES[index]
    path = OUT / filename
    ready = path.exists() and path.stat().st_size > 4096
    if not ready and time.monotonic() - started < 120:
        return
    records.append({"file": str(path), "material_mode": material_mode,
                    "bytes": path.stat().st_size if path.exists() else 0,
                    "sha256": sha256(path) if ready else None,
                    "status": "CAPTURE_PASS" if ready else "CAPTURE_FAIL"})
    index += 1
    if index < len(CAPTURES):
        begin_capture()
        return
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    finish()


begin_capture()
handle = unreal.register_slate_post_tick_callback(tick)
