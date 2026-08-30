"""Headless native SceneCapture2D render of the v041 portal-press camera.

This bypasses Unreal's editor high-resolution viewport queue, which is known
to hang when the editor window is intentionally hidden.  The capture actor and
render target are transient and are destroyed before exit; no map save occurs.
"""
import hashlib
import json
from pathlib import Path
import time

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
CAMERA_LABEL = "CAM v003 | compact press hero"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "CompactV003_s02_portal_lightingprobe_v044_dx12"
OUT = ROOT / "02_s02_portal_press_scene_capture.exr"
RECEIPT = ROOT / "scene_capture_receipt.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
START = time.monotonic()
HANDLE = None
CAPTURE = None
TARGET = None
TEMP_LIGHTS = []
EXPORTED = False
EXPORT_STARTED = 0.0
LAST_SIZE = -1
STABLE_AT = 0.0


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def finish(status, **extra):
    global HANDLE, CAPTURE
    if CAPTURE is not None:
        unreal.EditorLevelLibrary.destroy_actor(CAPTURE)
        CAPTURE = None
    for light in TEMP_LIGHTS:
        unreal.EditorLevelLibrary.destroy_actor(light)
    for path, expected in EXPECTED.items():
        if digest(path) != expected:
            status = "FAIL__PROTECTED_MAP_CHANGED_DURING_SCENE_CAPTURE"
            extra["protected_map_mismatch"] = str(path)
    RECEIPT.write_text(json.dumps({
        "status": status,
        "map": MAP,
        "camera": CAMERA_LABEL,
        "render_path": str(OUT),
        "capture_method": "native_scene_capture_2d_transient",
        "no_map_save": True,
        **extra,
    }, indent=2), encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("Refusing to overwrite v039 native-scene-capture evidence")
    for path, expected in EXPECTED.items():
        if digest(path) != expected:
            raise RuntimeError("Protected baseline changed before scene capture: " + str(path))
    ROOT.mkdir(parents=True, exist_ok=True)
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        raise RuntimeError("Could not load v003 candidate")
    camera = next((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL), None)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Named v039 camera unavailable")
    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in ("viewmode lit", "r.Streaming.FullyLoadUsedTextures 1", "sg.AntiAliasingQuality 4", "sg.ShadowQuality 3", "sg.GlobalIlluminationQuality 3"):
        unreal.SystemLibrary.execute_console_command(world, command)
    # The 5.8 Python surface does not expose TextureRenderTarget2D's native
    # InitAutoFormat.  CanvasRenderTarget2D is a TextureRenderTarget2D
    # subclass with an exposed transient factory and is accepted by capture.
    TARGET = unreal.CanvasRenderTarget2D.create_canvas_render_target2d(world, unreal.CanvasRenderTarget2D, 1920, 1080)
    if not isinstance(TARGET, unreal.TextureRenderTarget2D):
        raise RuntimeError("Could not create transient native render target")
    CAPTURE = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
    if not isinstance(CAPTURE, unreal.SceneCapture2D):
        raise RuntimeError("Could not create transient native scene capture")
    component = CAPTURE.capture_component2d
    component.texture_target = TARGET
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    component.fov_angle = 43.6
    component.capture_every_frame = False
    component.capture_on_movement = False
    # Let the candidate's B_stylized unbound post-process volume provide its
    # approved fixed exposure; the transient capture itself adds no look.
    component.post_process_blend_weight = 0.0
    CAPTURE.set_actor_hidden_in_game(True)
    # Transient probe only: no map save.  These broadly front-light the
    # candidate so the capture can distinguish light placement from exposure.
    for location, intensity in (
        (unreal.Vector(-4900.0, -3100.0, 2600.0), 6500.0),
        (unreal.Vector(-1850.0, -2600.0, 1800.0), 3500.0),
        (unreal.Vector(-2700.0, 1600.0, 3800.0), 2500.0),
    ):
        light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
        light_component = light.get_component_by_class(unreal.LightComponent)
        light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light_component.set_intensity(intensity)
        light_component.set_editor_property("attenuation_radius", 6000.0)
        light_component.set_light_color(unreal.LinearColor(1.0, 0.92, 0.78, 1.0))
        TEMP_LIGHTS.append(light)
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def tick(_delta):
        global EXPORTED, EXPORT_STARTED, LAST_SIZE, STABLE_AT
        elapsed = time.monotonic() - START
        if elapsed >= 8.0 and not EXPORTED:
            EXPORTED = True
            EXPORT_STARTED = time.monotonic()
            try:
                component.capture_scene()
                options = unreal.ImageWriteOptions(format=unreal.DesiredImageFormat.EXR, compression_quality=0, overwrite_file=False, async_=False)
                unreal.ImageWriteBlueprintLibrary.export_to_disk(TARGET, str(OUT), options)
            except Exception as exc:
                finish("FAIL__V039_NATIVE_SCENE_CAPTURE", error=repr(exc), elapsed_seconds=round(elapsed, 2))
                return
            unreal.log("PRESSSHOP_V039_SCENECAPTURE_EXPORT_REQUESTED")
        elif EXPORTED and OUT.is_file() and OUT.stat().st_size >= 4096:
            size = OUT.stat().st_size
            now = time.monotonic()
            if size != LAST_SIZE:
                LAST_SIZE, STABLE_AT = size, now
            elif now - STABLE_AT >= 6.0 and now - EXPORT_STARTED >= 6.0:
                finish("PASS__V039_NATIVE_SCENE_CAPTURE", bytes=size, sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(), elapsed_seconds=round(elapsed, 2))
        elif elapsed >= 75.0:
            finish("FAIL__V039_NATIVE_SCENE_CAPTURE", error="SceneCapture2D did not export a valid PNG", elapsed_seconds=round(elapsed, 2))

    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    ROOT.mkdir(parents=True, exist_ok=True)
    finish("FAIL__V039_NATIVE_SCENE_CAPTURE", error=repr(exc))
