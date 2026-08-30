"""Capture visual acceptance views for the refined 2126 press and outbound flow."""
import hashlib
import json
from pathlib import Path
import time

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
CAMERA_LABEL = "CAM | 2126 full hall fixed game view"
ROOT = PROJECT / "Saved" / "ValidationScreenshots" / "PressShop2126" / "FullHall_v001"
RECEIPT = ROOT / "52_53_refined_press_and_outbound_v002_receipt.json"
SHOTS = [
    {
        "name": "registered_press_train",
        "path": ROOT / "52_registered_master_press_train_refined_v002.png",
        "focus": unreal.Vector(-3500.0, 2550.0, 500.0),
        "ortho_width_cm": 11000.0,
    },
    {
        "name": "outbound_hover_convoy",
        "path": ROOT / "53_outbound_hover_convoy_refined_v002.png",
        "focus": unreal.Vector(3200.0, 4495.0, 0.0),
        "ortho_width_cm": 6200.0,
    },
]
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap":
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap":
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
START = time.monotonic()
HANDLE = None
CAPTURE = None
TARGET = None
CAMERA_FORWARD = None
SHOT_INDEX = 0
SHOT_STARTED_AT = 0.0
EXPORTED = False
LAST_SIZE = -1
STABLE_AT = 0.0
RESULTS = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def configure_shot(shot):
    global SHOT_STARTED_AT, EXPORTED, LAST_SIZE, STABLE_AT
    focus = shot["focus"]
    location = unreal.Vector(
        focus.x - CAMERA_FORWARD.x * 9000.0,
        focus.y - CAMERA_FORWARD.y * 9000.0,
        focus.z - CAMERA_FORWARD.z * 9000.0,
    )
    CAPTURE.set_actor_location(location, False, False)
    CAPTURE.capture_component2d.ortho_width = shot["ortho_width_cm"]
    SHOT_STARTED_AT = time.monotonic()
    EXPORTED = False
    LAST_SIZE = -1
    STABLE_AT = 0.0


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
        "map_saved": False,
        "protected_sha256_after": {str(path): digest(path) for path in PROTECTED},
        "shots": RESULTS,
        **extra,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


try:
    ROOT.mkdir(parents=True, exist_ok=True)
    if RECEIPT.exists() or any(shot["path"].exists() for shot in SHOTS):
        raise RuntimeError("refusing to overwrite refined visual proof")
    before = {str(path): digest(path) for path in PROTECTED}
    for path, expected in PROTECTED.items():
        if before[str(path)] != expected:
            raise RuntimeError("protected authority missing or changed: " + str(path))
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        raise RuntimeError("could not load isolated FullHall candidate")
    actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
    camera = actors.get(CAMERA_LABEL)
    if not isinstance(camera, unreal.CameraActor):
        raise RuntimeError("fixed game camera unavailable")
    for required in (
        "2126 PRESS | registered continuous S01-S04 master sprite",
        "2126 OUTBOUND | detailed finished-panel hover pallet sprite A",
        "2126 OUTBOUND | detailed finished-panel hover pallet sprite B",
        "2126 OUTBOUND | detailed finished-panel hover pallet sprite C",
    ):
        if required not in actors:
            raise RuntimeError("required refined visual actor missing: " + required)
    for forbidden in (
        "BP_LB_CR01_CleaningAMR_v0640",
        "BP_LB_CR01_CleaningAMR_v0641",
        "LB-CR01-01",
        "LB-CR01-02",
        "2126 TRANSFER | floor guide rail operator",
        "2126 TRANSFER | floor guide rail service",
    ):
        if forbidden in actors:
            raise RuntimeError("legacy clutter still present: " + forbidden)

    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in (
        "viewmode lit",
        "r.Streaming.FullyLoadUsedTextures 1",
        "sg.AntiAliasingQuality 4",
        "sg.ShadowQuality 3",
        "r.ScreenPercentage 100",
    ):
        unreal.SystemLibrary.execute_console_command(world, command)
    TARGET = unreal.CanvasRenderTarget2D.create_canvas_render_target2d(
        world, unreal.CanvasRenderTarget2D, 1920, 1080)
    TARGET.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    TARGET.update_resource()
    CAMERA_FORWARD = unreal.MathLibrary.get_forward_vector(camera.get_actor_rotation())
    CAPTURE = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SceneCapture2D, unreal.Vector(), camera.get_actor_rotation())
    component = CAPTURE.capture_component2d
    component.texture_target = TARGET
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    component.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.post_process_blend_weight = 0.0
    configure_shot(SHOTS[0])
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def tick(_delta):
        global SHOT_INDEX, EXPORTED, LAST_SIZE, STABLE_AT
        elapsed_total = time.monotonic() - START
        shot = SHOTS[SHOT_INDEX]
        elapsed_shot = time.monotonic() - SHOT_STARTED_AT
        if elapsed_shot >= 12.0 and not EXPORTED:
            EXPORTED = True
            try:
                component.capture_scene()
                options = unreal.ImageWriteOptions(
                    format=unreal.DesiredImageFormat.PNG,
                    compression_quality=0,
                    overwrite_file=False,
                    async_=False,
                )
                unreal.ImageWriteBlueprintLibrary.export_to_disk(TARGET, str(shot["path"]), options)
            except Exception as exc:
                finish("FAIL_CAPTURE", shot=shot["name"], error=repr(exc))
        elif EXPORTED and shot["path"].is_file() and shot["path"].stat().st_size >= 4096:
            size = shot["path"].stat().st_size
            now = time.monotonic()
            if size != LAST_SIZE:
                LAST_SIZE, STABLE_AT = size, now
            elif now - STABLE_AT >= 4.0:
                RESULTS.append({
                    "name": shot["name"],
                    "path": str(shot["path"]),
                    "bytes": size,
                    "sha256": digest(shot["path"]),
                    "focus_cm": [shot["focus"].x, shot["focus"].y, shot["focus"].z],
                    "camera_rotation": [-60.0, 57.63, 0.0],
                    "orthographic_width_cm": shot["ortho_width_cm"],
                })
                SHOT_INDEX += 1
                if SHOT_INDEX >= len(SHOTS):
                    after = {str(path): digest(path) for path in PROTECTED}
                    if after != before:
                        finish("FAIL_PROTECTED_MAP_CHANGED")
                    else:
                        finish("PASS_CAPTURE", elapsed_seconds=round(elapsed_total, 2))
                else:
                    configure_shot(SHOTS[SHOT_INDEX])
        elif elapsed_total >= 120.0:
            finish("FAIL_CAPTURE_TIMEOUT", elapsed_seconds=round(elapsed_total, 2))

    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    finish("FAIL_CAPTURE", error=repr(exc))
