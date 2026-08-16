"""Transient real-RHI Paint Shop lighting comparison; never saves Content."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap"
EXPECTED_MAP_SHA256 = "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT_DIR = ROOT / "Saved/Audits/PaintShop/Experimental_v001/LightingCalibration_v001" / STAMP
RECEIPT = OUT_DIR / "lighting_calibration_v001.json"

# Values deliberately bracket the current overexposed 6 x 12,000 lm scene.
OPTIONS = (
    {"name": "A_balanced", "rect_lumens": 2500.0, "sun": 0.45, "sky": 0.35,
     "exposure_bias": -0.25},
    {"name": "B_stylized", "rect_lumens": 1200.0, "sun": 0.30, "sky": 0.20,
     "exposure_bias": -0.50},
    {"name": "C_moody", "rect_lumens": 700.0, "sun": 0.20, "sky": 0.12,
     "exposure_bias": -0.75},
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def file_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size >= 10_000


def png_dimensions(path: Path):
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return [int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")]


def actors_of(world, actor_class):
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, actor_class))


def apply_option(world, option):
    rects = actors_of(world, unreal.RectLight)
    suns = actors_of(world, unreal.DirectionalLight)
    skies = actors_of(world, unreal.SkyLight)
    volumes = actors_of(world, unreal.PostProcessVolume)
    if len(rects) != 6 or len(suns) != 1 or len(skies) != 1 or len(volumes) != 1:
        raise RuntimeError(
            f"Lighting actor count drift: rect={len(rects)} sun={len(suns)} "
            f"sky={len(skies)} pp={len(volumes)}")
    for actor in rects:
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            raise RuntimeError("Paint RectLight has no RectLightComponent")
        component.set_editor_property("intensity", option["rect_lumens"])
    sun = suns[0].get_component_by_class(unreal.DirectionalLightComponent)
    sky = skies[0].get_component_by_class(unreal.SkyLightComponent)
    if sun is None or sky is None:
        raise RuntimeError("Paint sun/skylight component missing")
    sun.set_editor_property("intensity", option["sun"])
    sky.set_editor_property("intensity", option["sky"])
    pp = volumes[0].get_editor_property("settings")
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", option["exposure_bias"])
    volumes[0].set_editor_property("settings", pp)


OUT_DIR.mkdir(parents=True, exist_ok=False)
if sha256(MAP_FILE) != EXPECTED_MAP_SHA256:
    raise RuntimeError("Paint map hash drift before transient lighting calibration")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load Paint map: {MAP}")

payload = {
    "$schema": "lineboss/audit/paint-shop/lighting-calibration-v001/v1",
    "status": "IN_PROGRESS",
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "map_sha256_before": sha256(MAP_FILE),
    "options": [],
    "failures": [],
}
phase = "wait_world"
phase_started = time.monotonic()
option_index = 0
settle_frames = 0
capture_task = None
capture_path = None
tick_handle = None


def finish(status: str, detail: str):
    global tick_handle
    payload["status"] = status
    payload["detail"] = detail
    payload["map_sha256_after"] = sha256(MAP_FILE)
    payload["map_hash_unchanged"] = payload["map_sha256_after"] == payload["map_sha256_before"]
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Paint map changed during transient calibration")
        payload["status"] = "FAIL__PAINT_SHOP_LIGHTING_CALIBRATION_V001"
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def fail(message: str):
    global phase, phase_started, capture_task
    payload["failures"].append(message)
    capture_task = None
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is not None:
        levels.editor_request_end_play()
        phase = "ending_failure"
        phase_started = time.monotonic()
    else:
        finish("FAIL__PAINT_SHOP_LIGHTING_CALIBRATION_V001", message)


def tick(_delta_seconds):
    global phase, phase_started, option_index, settle_frames, capture_task, capture_path
    now = time.monotonic()
    try:
        world = unreal.EditorLevelLibrary.get_game_world()
        if phase == "wait_world":
            if world is None:
                if now - phase_started > 45.0:
                    raise RuntimeError("Paint PIE world did not start")
                return
            pawns = actors_of(world, unreal.LBPaintShopManagementPawn)
            bootstraps = actors_of(world, unreal.LBPaintShopPrototypeWorldBootstrap)
            if len(pawns) != 1 or len(bootstraps) != 1 or not bootstraps[0].is_ready():
                if now - phase_started > 45.0:
                    raise RuntimeError("Paint player shell/bootstrap did not become ready")
                return
            phase = "apply_option"
        if phase == "apply_option":
            if option_index >= len(OPTIONS):
                levels.editor_request_end_play()
                phase = "ending_success"
                phase_started = now
                return
            apply_option(world, OPTIONS[option_index])
            settle_frames = 0
            phase = "settle"
            return
        if phase == "settle":
            settle_frames += 1
            if settle_frames < 30:
                return
            option = OPTIONS[option_index]
            capture_path = OUT_DIR / f"{option_index + 1:02d}_{option['name']}.png"
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            capture_task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(capture_path), force_game_view=False)
            if not capture_task.is_valid_task():
                raise RuntimeError(f"Invalid screenshot task for {option['name']}")
            phase = "wait_capture"
            phase_started = now
            return
        if phase == "wait_capture":
            if now - phase_started > 45.0:
                raise RuntimeError(f"Screenshot timed out: {capture_path.name}")
            if now - phase_started < 2.0 or not capture_task.is_task_done() or not file_ready(capture_path):
                return
            dimensions = png_dimensions(capture_path)
            if dimensions != [1920, 1080]:
                raise RuntimeError(f"Wrong screenshot dimensions: {dimensions}")
            option = dict(OPTIONS[option_index])
            option.update({
                "path": str(capture_path),
                "bytes": capture_path.stat().st_size,
                "sha256": sha256(capture_path),
                "dimensions": dimensions,
            })
            payload["options"].append(option)
            capture_task = None
            option_index += 1
            phase = "apply_option"
            return
        if phase in {"ending_success", "ending_failure"}:
            if world is not None:
                if now - phase_started > 30.0:
                    raise RuntimeError("Paint PIE did not end after lighting calibration")
                return
            if phase == "ending_success":
                finish("PASS__TRANSIENT_PAINT_SHOP_LIGHTING_CALIBRATION_V001",
                       "Three real-RHI lighting options captured without saving Content")
            else:
                finish("FAIL__PAINT_SHOP_LIGHTING_CALIBRATION_V001", payload["failures"][-1])
    except Exception as exc:
        fail(str(exc))


try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    levels.editor_request_begin_play()
except Exception:
    if tick_handle is not None:
        try:
            unreal.unregister_slate_post_tick_callback(tick_handle)
        except Exception:
            pass
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    raise
