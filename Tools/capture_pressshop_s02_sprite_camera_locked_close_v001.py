"""Capture S02 close-up from the exact camera-locked 60-degree 2.5D basis."""
import hashlib
import json
from pathlib import Path
import time

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v006_TopdownSprite/Maps/LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "Factorio2p5DFull_v006TopdownSprite"
OUT = ROOT / "01_s02_sprite_topdown_close.png"
RECEIPT = ROOT / "capture_s02_sprite_topdown_close_receipt.json"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
START = time.monotonic()
HANDLE = None
CAPTURE = None
TARGET = None
EXPORTED = False
LAST_SIZE = -1
STABLE_AT = 0.0

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

def finish(status, **extra):
    global HANDLE, CAPTURE
    if CAPTURE is not None:
        unreal.EditorLevelLibrary.destroy_actor(CAPTURE)
        CAPTURE = None
    ROOT.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps({
        "status": status, "map": MAP, "source_camera": CAMERA_LABEL,
        "sprite": SPRITE_LABEL, "render_path": str(OUT),
        "capture_basis": "same pitch and yaw as the actual locked player camera; only orthographic centre and width differ",
        "no_map_save": True,
        "protected_sha256_after": {name: digest(path) for name, path in PROTECTED.items()},
        **extra,
    }, indent=2), encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("refusing to overwrite camera-locked close proof")
    if any(not path.is_file() for path in PROTECTED.values()):
        raise RuntimeError("protected map missing")
    protected_before = {name: digest(path) for name, path in PROTECTED.items()}
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        raise RuntimeError("could not load camera-locked candidate")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    camera = next((actor for actor in actors if actor.get_actor_label() == CAMERA_LABEL), None)
    sprite = next((actor for actor in actors if actor.get_actor_label() == SPRITE_LABEL), None)
    if not isinstance(camera, unreal.CameraActor) or not isinstance(sprite, unreal.StaticMeshActor):
        raise RuntimeError("locked camera or S02 sprite unavailable")
    rotation = camera.get_actor_rotation()
    forward = unreal.MathLibrary.get_forward_vector(rotation)
    sprite_location = sprite.get_actor_location()
    location = unreal.Vector(
        sprite_location.x - forward.x * 20000.0,
        sprite_location.y - forward.y * 20000.0,
        sprite_location.z - forward.z * 20000.0,
    )
    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in ("viewmode lit", "r.Streaming.FullyLoadUsedTextures 1", "sg.AntiAliasingQuality 4", "sg.ShadowQuality 2"):
        unreal.SystemLibrary.execute_console_command(world, command)
    TARGET = unreal.CanvasRenderTarget2D.create_canvas_render_target2d(
        world, unreal.CanvasRenderTarget2D, 1920, 1080)
    TARGET.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    TARGET.update_resource()
    CAPTURE = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, location, rotation)
    if not isinstance(TARGET, unreal.TextureRenderTarget2D) or not isinstance(CAPTURE, unreal.SceneCapture2D):
        raise RuntimeError("could not create native capture resources")
    component = CAPTURE.capture_component2d
    component.texture_target = TARGET
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    component.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
    component.ortho_width = 2500.0
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.post_process_blend_weight = 0.0
    CAPTURE.set_actor_hidden_in_game(True)
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def tick(_delta):
        global EXPORTED, LAST_SIZE, STABLE_AT
        elapsed = time.monotonic() - START
        if elapsed >= 10.0 and not EXPORTED:
            EXPORTED = True
            try:
                component.capture_scene()
                options = unreal.ImageWriteOptions(
                    format=unreal.DesiredImageFormat.PNG, compression_quality=0,
                    overwrite_file=False, async_=False)
                unreal.ImageWriteBlueprintLibrary.export_to_disk(TARGET, str(OUT), options)
            except Exception as exc:
                finish("FAIL__S02_CAMERA_LOCKED_CLOSE_CAPTURE", error=repr(exc), elapsed_seconds=round(elapsed, 2))
        elif EXPORTED and OUT.is_file() and OUT.stat().st_size >= 4096:
            size = OUT.stat().st_size
            now = time.monotonic()
            if size != LAST_SIZE:
                LAST_SIZE, STABLE_AT = size, now
            elif now - STABLE_AT >= 5.0:
                after = {name: digest(path) for name, path in PROTECTED.items()}
                if after != protected_before:
                    finish("FAIL__PROTECTED_MAP_CHANGED_DURING_S02_CLOSE_CAPTURE",
                           protected_sha256_before=protected_before, protected_sha256_after=after)
                else:
                    finish("PASS__S02_CAMERA_LOCKED_CLOSE_CAPTURE",
                           bytes=size, sha256=digest(OUT), elapsed_seconds=round(elapsed, 2),
                           protected_sha256_before=protected_before,
                           camera_rotation=[round(rotation.pitch, 3), round(rotation.yaw, 3), round(rotation.roll, 3)],
                           close_capture_location_cm=[round(location.x, 3), round(location.y, 3), round(location.z, 3)],
                           orthographic_width_cm=2500.0)
        elif elapsed >= 70.0:
            finish("FAIL__S02_CAMERA_LOCKED_CLOSE_CAPTURE",
                   error="SceneCapture2D did not export a valid PNG", elapsed_seconds=round(elapsed, 2))
    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish("FAIL__S02_CAMERA_LOCKED_CLOSE_CAPTURE", error=repr(exc))
