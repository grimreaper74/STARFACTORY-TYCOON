"""Capture the complete v007 sprite Press Shop with Unreal's native SceneCapture2D."""
import hashlib
import json
from pathlib import Path
import time

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007/Maps/LB_PressShop_Factorio2p5D_IndividualSprites_v007"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
ROOT = PROJECT / "Saved" / "ValidationScreenshots" / "PressShop2126" / "IndividualSprites_v007"
OUT = ROOT / "01_full_press_shop_overview.png"
RECEIPT = ROOT / "capture_full_press_shop_overview_receipt.json"
PROTECTED_MAPS = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
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
        "status": status,
        "map": MAP,
        "source_camera": CAMERA_LABEL,
        "render_path": str(OUT),
        "capture_contract": "same fixed -60 degree game-camera basis; overview only; no map save",
        "protected_sha256_after": {str(path): digest(path) for path in PROTECTED_MAPS},
        **extra,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("refusing to overwrite overview proof")
    for path, expected in PROTECTED_MAPS.items():
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError("protected map missing or changed: {}".format(path))
    before = {str(path): digest(path) for path in PROTECTED_MAPS}
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        raise RuntimeError("could not load v007 candidate")
    camera = next((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL), None)
    if not isinstance(camera, unreal.CameraActor):
        raise RuntimeError("overview camera unavailable")
    rotation = camera.get_actor_rotation()
    if abs(rotation.pitch + 60.0) > 0.2:
        raise RuntimeError("camera pitch is not locked at -60 degrees")
    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in ("viewmode lit", "r.Streaming.FullyLoadUsedTextures 1", "sg.AntiAliasingQuality 4", "sg.ShadowQuality 2"):
        unreal.SystemLibrary.execute_console_command(world, command)
    TARGET = unreal.CanvasRenderTarget2D.create_canvas_render_target2d(world, unreal.CanvasRenderTarget2D, 1920, 1080)
    TARGET.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    TARGET.update_resource()
    CAPTURE = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), rotation)
    if not isinstance(CAPTURE, unreal.SceneCapture2D):
        raise RuntimeError("could not create native capture actor")
    component = CAPTURE.capture_component2d
    component.texture_target = TARGET
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    component.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
    component.ortho_width = 16000.0
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.post_process_blend_weight = 0.0
    CAPTURE.set_actor_hidden_in_game(True)
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def tick(_delta):
        global EXPORTED, LAST_SIZE, STABLE_AT
        elapsed = time.monotonic() - START
        if elapsed >= 12.0 and not EXPORTED:
            EXPORTED = True
            try:
                component.capture_scene()
                options = unreal.ImageWriteOptions(format=unreal.DesiredImageFormat.PNG, compression_quality=0, overwrite_file=False, async_=False)
                unreal.ImageWriteBlueprintLibrary.export_to_disk(TARGET, str(OUT), options)
            except Exception as exc:
                finish("FAIL__FULL_PRESS_SHOP_OVERVIEW_CAPTURE", error=repr(exc), elapsed_seconds=round(elapsed, 2))
        elif EXPORTED and OUT.is_file() and OUT.stat().st_size >= 4096:
            size = OUT.stat().st_size
            now = time.monotonic()
            if size != LAST_SIZE:
                LAST_SIZE, STABLE_AT = size, now
            elif now - STABLE_AT >= 5.0:
                after = {str(path): digest(path) for path in PROTECTED_MAPS}
                if after != before:
                    finish("FAIL__PROTECTED_MAP_CHANGED_DURING_OVERVIEW_CAPTURE", protected_sha256_before=before, protected_sha256_after=after)
                else:
                    finish("PASS__FULL_PRESS_SHOP_OVERVIEW_CAPTURE", bytes=size, sha256=digest(OUT), elapsed_seconds=round(elapsed, 2), protected_sha256_before=before, camera_rotation=[round(rotation.pitch, 3), round(rotation.yaw, 3), round(rotation.roll, 3)], orthographic_width_cm=16000.0)
        elif elapsed >= 80.0:
            finish("FAIL__FULL_PRESS_SHOP_OVERVIEW_CAPTURE", error="SceneCapture2D did not export a valid PNG", elapsed_seconds=round(elapsed, 2))
    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish("FAIL__FULL_PRESS_SHOP_OVERVIEW_CAPTURE", error=repr(exc))
