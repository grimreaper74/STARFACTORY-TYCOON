"""Capture the S02 sprite-art gate without saving its candidate map."""
import hashlib
import json
from pathlib import Path
import time

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v002_SpriteArt/Maps/LB_PressShop_Factorio2p5D_Full_v002_SpriteArt"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "Factorio2p5DFull_v002SpriteArt"
OUT = ROOT / "01_s02_sprite_art_overview.exr"
RECEIPT = ROOT / "capture_receipt.json"
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
    protected = {name: digest(path) for name, path in PROTECTED.items()}
    if any(not path.is_file() for path in PROTECTED.values()):
        status = "FAIL__PROTECTED_MAP_MISSING_DURING_SPRITE_CAPTURE"
    ROOT.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps({
        "status": status,
        "map": MAP,
        "camera": CAMERA_LABEL,
        "render_path": str(OUT),
        "capture_method": "native_scene_capture_2d_transient",
        "no_map_save": True,
        "protected_sha256_after": protected,
        **extra,
    }, indent=2), encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("refusing to overwrite S02 sprite-art capture evidence")
    if any(not path.is_file() for path in PROTECTED.values()):
        raise RuntimeError("a protected map is missing")
    protected_before = {name: digest(path) for name, path in PROTECTED.items()}
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        raise RuntimeError("could not load sprite-art candidate")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    camera = next((actor for actor in actors if actor.get_actor_label() == CAMERA_LABEL), None)
    sprite = next((actor for actor in actors if actor.get_actor_label() == "2.5D sprite art | S02 draw-form portal press"), None)
    if not isinstance(camera, unreal.CameraActor) or not isinstance(sprite, unreal.StaticMeshActor):
        raise RuntimeError("overview camera or S02 sprite actor unavailable")
    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in ("viewmode lit", "r.Streaming.FullyLoadUsedTextures 1", "sg.AntiAliasingQuality 4", "sg.ShadowQuality 2"):
        unreal.SystemLibrary.execute_console_command(world, command)
    TARGET = unreal.CanvasRenderTarget2D.create_canvas_render_target2d(world, unreal.CanvasRenderTarget2D, 1920, 1080)
    CAPTURE = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
    if not isinstance(TARGET, unreal.TextureRenderTarget2D) or not isinstance(CAPTURE, unreal.SceneCapture2D):
        raise RuntimeError("could not create native capture resources")
    component = CAPTURE.capture_component2d
    component.texture_target = TARGET
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    component.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
    component.ortho_width = camera.get_editor_property("camera_component").get_editor_property("ortho_width")
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
                options = unreal.ImageWriteOptions(format=unreal.DesiredImageFormat.EXR, compression_quality=0, overwrite_file=False, async_=False)
                unreal.ImageWriteBlueprintLibrary.export_to_disk(TARGET, str(OUT), options)
            except Exception as exc:
                finish("FAIL__S02_SPRITE_ART_NATIVE_CAPTURE", error=repr(exc), elapsed_seconds=round(elapsed, 2))
        elif EXPORTED and OUT.is_file() and OUT.stat().st_size >= 4096:
            size = OUT.stat().st_size
            now = time.monotonic()
            if size != LAST_SIZE:
                LAST_SIZE, STABLE_AT = size, now
            elif now - STABLE_AT >= 5.0:
                after = {name: digest(path) for name, path in PROTECTED.items()}
                if after != protected_before:
                    finish("FAIL__PROTECTED_MAP_CHANGED_DURING_S02_SPRITE_CAPTURE", protected_sha256_before=protected_before, protected_sha256_after=after)
                else:
                    finish("PASS__S02_SPRITE_ART_NATIVE_CAPTURE", bytes=size, sha256=digest(OUT), elapsed_seconds=round(elapsed, 2), protected_sha256_before=protected_before)
        elif elapsed >= 70.0:
            finish("FAIL__S02_SPRITE_ART_NATIVE_CAPTURE", error="SceneCapture2D did not export a valid EXR", elapsed_seconds=round(elapsed, 2))
    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish("FAIL__S02_SPRITE_ART_NATIVE_CAPTURE", error=repr(exc))
