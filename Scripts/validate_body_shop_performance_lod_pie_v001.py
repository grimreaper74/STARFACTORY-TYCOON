"""Capture fail-closed numeric performance and renderer-selected LOD evidence.

This is intentionally an isolated Body Shop PIE capture lane.  It does not save
Content, change project configuration, or force component LODs.  Unreal's CSV
Profiler supplies fixed-frame timing/memory samples and DumpDetailedPrimitives
supplies the renderer's actual per-view LOD, triangle, and draw counts.

The companion ``analyze_body_shop_performance_lod_v001.py`` owns all budgets and
turns these raw files into the final PASS/FAIL receipt.  Authored-mesh LOD
metadata is snapshotted in the editor before PIE starts; renderer-selected LODs
remain proven independently by the per-view primitive dumps.
"""

from __future__ import annotations

from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

import unreal


raise RuntimeError(
    "BLOCKED__BODY_SHOP_1920X1080_EDITOR_PIE_PERFORMANCE_LOD_V001: "
    "UE 5.8 editor PIE could not establish an exact 1920x1080 real-RHI viewport "
    "on the 1280x720 host without unsafe editor DPI/native-window manipulation; "
    "use the separately designed packaged Development capture seam instead"
)


unreal.EditorPythonScripting.set_keep_python_script_alive(True)

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
STAMP = os.environ.get("LB_BODYSHOP_PERF_LOD_STAMP") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_DIR = ROOT / "Saved/Audits/BodyShop/Experimental_v001/PerformanceLODValidation" / STAMP
RAW_DIR = RUN_DIR / "Raw"
CAPTURE_RECEIPT = RUN_DIR / "performance_lod_raw_capture_v001.json"
CSV_SOURCE_DIR = ROOT / "Saved/Profiling/CSV"
PRIMITIVE_SOURCE_DIR = ROOT / "Saved/Profiling/Primitives"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
STATIC_MESHES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

PROFILE_FRAMES = 300
VIEW_SETTLE_FRAMES = 120
PROFILE_FINALISE_MARGIN_FRAMES = 90
PROFILE_STABLE_SECONDS = 2.0
TIMEOUT_SECONDS = 210.0
EXPECTED_VIEWPORT = (1920, 1080)
VIEWPORT_RESIZE_SETTLE_TICKS = 30
MAX_VIEWPORT_RESIZE_ATTEMPTS = 5

ROBOT_COMPONENT_NAMES = {
    "BasePresentation", "J1Presentation", "J2Presentation", "J3Presentation",
    "J4Presentation", "J5Presentation", "J6Presentation", "ToolPresentation",
}
EXPECTED_SLOTS = {"ROBOT_HND_01", "ROBOT_WELD_LEFT", "ROBOT_WELD_RIGHT"}
TARGET_CELL_DEFINITIONS = {"BW012_VISION_GATE_BASIC": "vision_gate"}
EXPECTED_TARGET_COMPONENT_COUNT = 25
EXPECTED_UNIQUE_MESH_COUNT = 10
EXPECTED_UNIQUE_MESHES = {
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.SM_LB_BodyShopRobotNative_J1_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.SM_LB_BodyShopRobotNative_J2_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.SM_LB_BodyShopRobotNative_J3_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.SM_LB_BodyShopRobotNative_J4_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.SM_LB_BodyShopRobotNative_J5_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.SM_LB_BodyShopRobotNative_J6_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001",
}
EDITOR_LOD_METADATA = {}

RUN_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
CSV_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
PRIMITIVE_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

MAP_SHA_BEFORE = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
payload = {
    "$schema": "cairnwell/body-shop/experimental-v001/performance-lod-raw-capture/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "IN_PROGRESS",
    "stamp": STAMP,
    "map": MAP,
    "map_sha256_before": MAP_SHA_BEFORE,
    "capture_contract": {
        "resolution": list(EXPECTED_VIEWPORT),
        "play_surface": "new_editor_window_pie",
        "viewport_size_authority": "APlayerController.GetViewportSize",
        "viewport_enforcement": "win32_resize_floating_pie_after_sane_window_placement",
        "profile_frames_per_view": PROFILE_FRAMES,
        "warmup_frames_per_view": VIEW_SETTLE_FRAMES,
        "rhi_required": True,
        "null_rhi_forbidden": True,
        "gpu_csv_stats_required": True,
        "forced_component_lod_forbidden": True,
        "editor_lod_metadata_phase": "pre_pie",
        "views": [
            {"id": "management", "definition": "process focus plus 2080 cm wider boom"},
            {"id": "focus", "definition": "authored FocusPrototypeProcess comparison camera"},
        ],
    },
    "engine_command_line": unreal.SystemLibrary.get_command_line(),
    "target_components": [],
    "views": {},
    "failures": [],
    "engine_api_notes": [
        "UStaticMeshComponent does not retain one universal current LOD because LOD is selected per FSceneView.",
        "DumpDetailedPrimitives is used because it records FPrimitiveSceneProxy::GetLOD for the rendered view.",
        "CSV Profiler GPU timing requires -csvGpuStats and a real RHI; NullRHI is rejected.",
        "The final analyzer fails if the RHI does not expose GPU timing or required memory/streaming counters.",
        "StaticMeshEditorSubsystem is intentionally queried before PIE because it can report zero source LODs for PIE-world component mesh references.",
        "Engine cube/cylinder conveyor and floor HISMs remain in scene performance totals but are not treated as authored imported-mesh LOD targets.",
        "The editor Alt+P command is pinned to New Editor Window (PIE); editor_request_begin_play is forbidden because UE 5.8 binds it to the docked active editor viewport.",
        "APlayerController.GetViewportSize is the authoritative game-render viewport size; no editor viewport dimensions are used.",
        "UE may clamp a newly-created PIE window to the host desktop; the Windows runner expands only the native PIE window after creation and rechecks the rendered viewport until it is exactly 1920x1080.",
    ],
}

started = time.monotonic()
tick_handle = None
tick_number = 0
phase = "wait_world"
phase_tick = 0
phase_time = started
active_view = None
profile_path = None
profile_size = -1
profile_size_changed_at = 0.0
primitive_baseline = set()
primitive_started_at_ns = 0
view_order = ["management", "focus"]
view_index = 0
viewport_resize_attempts = []
payload["capture_contract"]["viewport_resize_attempts"] = viewport_resize_attempts


def actors_of(world, cls):
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, cls))


def vec(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


def rot(value):
    return {
        "pitch": round(float(value.pitch), 3),
        "yaw": round(float(value.yaw), 3),
        "roll": round(float(value.roll), 3),
    }


def game_viewport_size(world):
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    if controller is None:
        raise RuntimeError("Possessed player controller is unavailable for game-viewport sizing")
    viewport_x, viewport_y = controller.get_viewport_size()
    return controller, (int(viewport_x), int(viewport_y))


def dpi_awareness(user32, context=None):
    user32.GetThreadDpiAwarenessContext.argtypes = []
    user32.GetThreadDpiAwarenessContext.restype = wintypes.HANDLE
    user32.GetAwarenessFromDpiAwarenessContext.argtypes = [wintypes.HANDLE]
    user32.GetAwarenessFromDpiAwarenessContext.restype = ctypes.c_int
    selected = context if context is not None else user32.GetThreadDpiAwarenessContext()
    return int(user32.GetAwarenessFromDpiAwarenessContext(selected))


def enable_physical_pixel_dpi_context():
    """Make the yet-to-be-created PIE HWND Per-Monitor-v2 DPI aware.

    The runner is a short-lived isolated editor process.  Keeping this thread
    context until process exit is intentional: a window's DPI context is fixed
    when its HWND is created, and restoring the previous context before Slate
    creates floating PIE would reintroduce 150% coordinate virtualization.
    """
    if os.name != "nt":
        raise RuntimeError("Exact floating-PIE DPI control requires Windows")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetThreadDpiAwarenessContext.argtypes = [wintypes.HANDLE]
    user32.SetThreadDpiAwarenessContext.restype = wintypes.HANDLE

    # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 is the signed pseudo-handle -4.
    target = wintypes.HANDLE(ctypes.c_void_p(-4).value)
    previous = user32.SetThreadDpiAwarenessContext(target)
    if not previous:
        error = ctypes.get_last_error()
        raise RuntimeError(
            "SetThreadDpiAwarenessContext(PER_MONITOR_AWARE_V2) failed "
            f"(Win32 error {error})"
        )
    current_awareness = dpi_awareness(user32)
    if current_awareness != 2:  # DPI_AWARENESS_PER_MONITOR_AWARE
        raise RuntimeError(
            "PIE creation thread is not per-monitor DPI aware after explicit override; "
            f"GetAwarenessFromDpiAwarenessContext returned {current_awareness}"
        )
    payload["capture_contract"]["dpi_awareness"] = {
        "creation_thread_context": "DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2",
        "awareness_value": current_awareness,
        "kept_until_process_exit": True,
        "coordinate_space": "physical_pixels",
    }


def visible_pie_windows():
    """Return this process's visible native floating-PIE windows, fail-closed."""
    if os.name != "nt":
        raise RuntimeError("Exact floating-PIE viewport enforcement requires Windows")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int

    rows = []
    process_id = os.getpid()

    @enum_proc
    def visit(hwnd, _lparam):
        owner_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
        if owner_pid.value != process_id or not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        title = buffer.value
        if " Preview [NetMode: " in title:
            rows.append({"hwnd": int(hwnd), "title": title})
        return True

    if not user32.EnumWindows(visit, 0):
        error = ctypes.get_last_error()
        raise RuntimeError(f"EnumWindows failed while locating floating PIE (Win32 error {error})")
    return rows


def resize_floating_pie_window(current_viewport):
    """Resize the PMv2 PIE HWND in physical pixels, allowing it offscreen."""
    candidates = visible_pie_windows()
    if len(candidates) != 1:
        titles = [row["title"] for row in candidates]
        raise RuntimeError(
            f"Expected exactly one visible floating PIE native window, found {len(candidates)}: {titles}"
        )

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    if dpi_awareness(user32) != 2:
        raise RuntimeError("Floating PIE resize thread lost Per-Monitor-v2 DPI awareness")
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    user32.GetDpiForWindow.argtypes = [wintypes.HWND]
    user32.GetDpiForWindow.restype = wintypes.UINT
    user32.GetWindowDpiAwarenessContext.argtypes = [wintypes.HWND]
    user32.GetWindowDpiAwarenessContext.restype = wintypes.HANDLE
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.AdjustWindowRectExForDpi.argtypes = [
        ctypes.POINTER(wintypes.RECT), wintypes.DWORD, wintypes.BOOL,
        wintypes.DWORD, wintypes.UINT,
    ]
    user32.AdjustWindowRectExForDpi.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL

    candidate = candidates[0]
    hwnd = wintypes.HWND(candidate["hwnd"])
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        error = ctypes.get_last_error()
        raise RuntimeError(f"GetWindowRect failed for floating PIE (Win32 error {error})")

    client_rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        error = ctypes.get_last_error()
        raise RuntimeError(f"GetClientRect failed for floating PIE (Win32 error {error})")
    dpi = int(user32.GetDpiForWindow(hwnd))
    if dpi <= 0:
        raise RuntimeError("GetDpiForWindow returned no DPI for floating PIE")
    window_awareness = dpi_awareness(
        user32,
        user32.GetWindowDpiAwarenessContext(hwnd),
    )
    if window_awareness != 2:
        raise RuntimeError(
            "Floating PIE HWND was not created Per-Monitor-v2 aware; "
            f"awareness={window_awareness} dpi={dpi}"
        )

    outer_size = (int(rect.right - rect.left), int(rect.bottom - rect.top))
    client_size = (
        int(client_rect.right - client_rect.left),
        int(client_rect.bottom - client_rect.top),
    )
    delta = (
        EXPECTED_VIEWPORT[0] - current_viewport[0],
        EXPECTED_VIEWPORT[1] - current_viewport[1],
    )
    if not viewport_resize_attempts:
        # First request: derive the physical outer size that provides a native
        # 1920x1080 client from this exact HWND's styles and monitor DPI.
        style = int(user32.GetWindowLongPtrW(hwnd, -16)) & 0xFFFFFFFF  # GWL_STYLE
        ex_style = int(user32.GetWindowLongPtrW(hwnd, -20)) & 0xFFFFFFFF  # GWL_EXSTYLE
        adjusted = wintypes.RECT(0, 0, EXPECTED_VIEWPORT[0], EXPECTED_VIEWPORT[1])
        if not user32.AdjustWindowRectExForDpi(
            ctypes.byref(adjusted), style, False, ex_style, dpi,
        ):
            error = ctypes.get_last_error()
            raise RuntimeError(
                f"AdjustWindowRectExForDpi failed for floating PIE (Win32 error {error})"
            )
        requested_outer = (
            int(adjusted.right - adjusted.left),
            int(adjusted.bottom - adjusted.top),
        )
    else:
        # Slate content can have a small in-client overlay.  Once the native
        # client is established, correct any residual with the exact rendered
        # viewport delta; all values are physical pixels under PMv2.
        requested_outer = (outer_size[0] + delta[0], outer_size[1] + delta[1])
    if requested_outer[0] <= 0 or requested_outer[1] <= 0:
        raise RuntimeError(f"Computed invalid native PIE window size: {requested_outer}")

    # SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOSENDCHANGING.
    # Suppressing WM_WINDOWPOSCHANGING prevents Slate/Windows from reapplying
    # work-area sizing.  The resulting window may extend below/right of the
    # 1280x720 host desktop; that is intentional for an offscreen RHI capture.
    flags = 0x0002 | 0x0004 | 0x0010 | 0x0400
    if not user32.SetWindowPos(
        hwnd, wintypes.HWND(0), 0, 0,
        requested_outer[0], requested_outer[1], flags,
    ):
        error = ctypes.get_last_error()
        raise RuntimeError(f"SetWindowPos failed for floating PIE (Win32 error {error})")

    return {
        "attempt": len(viewport_resize_attempts) + 1,
        "hwnd": f"0x{candidate['hwnd']:X}",
        "title": candidate["title"],
        "viewport_before": list(current_viewport),
        "native_outer_before": list(outer_size),
        "native_client_before": list(client_size),
        "window_dpi": dpi,
        "window_awareness": window_awareness,
        "viewport_delta_requested": list(delta),
        "native_outer_requested": list(requested_outer),
    }


def game_asset_file(object_path):
    package_path = object_path.split(".", 1)[0]
    if not package_path.startswith("/Game/"):
        raise RuntimeError(f"LOD target is not a project asset: {object_path}")
    return ROOT / "Content" / (package_path[len("/Game/"):] + ".uasset")


def snapshot_editor_lod_metadata():
    """Capture immutable authored-mesh metadata before entering PIE."""
    rows = {}
    for object_path in sorted(EXPECTED_UNIQUE_MESHES):
        mesh = unreal.load_asset(object_path)
        if mesh is None or not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"Could not load authored StaticMesh before PIE: {object_path}")
        if mesh.get_path_name() != object_path:
            raise RuntimeError(
                f"Loaded authored mesh identity drifted: expected {object_path}, got {mesh.get_path_name()}"
            )
        lod_count = int(mesh.get_num_lods())
        if lod_count < 1:
            raise RuntimeError(f"Authored mesh reports no source LOD before PIE: {object_path}")
        screen_sizes = [
            round(float(value), 6)
            for value in STATIC_MESHES.get_lod_screen_sizes(mesh)
        ]
        if len(screen_sizes) != lod_count:
            raise RuntimeError(
                f"Authored mesh LOD screen-size count drifted before PIE: {object_path} "
                f"({len(screen_sizes)} screen sizes for {lod_count} LODs)"
            )
        triangles = [int(mesh.get_num_triangles(index)) for index in range(lod_count)]
        vertices = [int(mesh.get_num_vertices(index)) for index in range(lod_count)]
        if any(value <= 0 for value in triangles + vertices):
            raise RuntimeError(f"Authored mesh has an empty source LOD before PIE: {object_path}")
        asset_file = game_asset_file(object_path)
        if not asset_file.is_file():
            raise RuntimeError(f"Authored mesh package is missing: {asset_file}")
        rows[object_path] = {
            "object_path": object_path,
            "lod_count": lod_count,
            "lod_screen_sizes": screen_sizes,
            "lod_triangles": triangles,
            "lod_vertices": vertices,
            "source_asset_file": str(asset_file),
            "source_asset_bytes": asset_file.stat().st_size,
            "source_asset_sha256": hashlib.sha256(asset_file.read_bytes()).hexdigest().upper(),
        }
    if len(rows) != EXPECTED_UNIQUE_MESH_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_UNIQUE_MESH_COUNT} authored meshes before PIE, found {len(rows)}"
        )
    return rows


def component_record(actor, component, category, identity):
    mesh = component.static_mesh
    if mesh is None:
        raise RuntimeError(f"Target component has no static mesh: {actor.get_full_name()}::{component.get_name()}")
    mesh_path = mesh.get_path_name()
    metadata = EDITOR_LOD_METADATA.get(mesh_path)
    if metadata is None:
        raise RuntimeError(
            f"Runtime target mesh was not pinned by the pre-PIE editor snapshot: {mesh_path}"
        )
    forced_lod = int(component.get_editor_property("forced_lod_model"))
    if forced_lod != 0:
        raise RuntimeError(
            f"Target component forces LOD {forced_lod - 1}; automatic selection proof is invalid: "
            f"{actor.get_full_name()}::{component.get_name()}"
        )
    return {
        "key": f"{identity}:{component.get_name()}",
        "category": category,
        "identity": identity,
        "actor_full_name": actor.get_full_name(),
        "actor_name": actor.get_name(),
        "component_name": component.get_name(),
        "mesh_path": mesh_path,
        "lod_count": metadata["lod_count"],
        "lod_screen_sizes": list(metadata["lod_screen_sizes"]),
        "lod_triangles": list(metadata["lod_triangles"]),
        "lod_vertices": list(metadata["lod_vertices"]),
        "lod_metadata_source": "editor_static_mesh_snapshot_pre_pie",
        "source_asset_sha256": metadata["source_asset_sha256"],
        "forced_lod_model": forced_lod,
    }


def build_target_manifest(world):
    robots = actors_of(world, unreal.LBBodyShopRobotActor)
    cells = actors_of(world, unreal.LBBodyShopCellActor)
    if len(robots) != 3:
        raise RuntimeError(f"Expected three Body Shop robots, found {len(robots)}")
    if {str(robot.get_slot_id()) for robot in robots} != EXPECTED_SLOTS:
        raise RuntimeError("Robot-slot set drifted before performance capture")

    rows = []
    for robot in sorted(robots, key=lambda value: str(value.get_slot_id())):
        slot = str(robot.get_slot_id())
        components = {
            component.get_name(): component
            for component in robot.get_components_by_class(unreal.StaticMeshComponent)
            if component.get_name() in ROBOT_COMPONENT_NAMES
        }
        if set(components) != ROBOT_COMPONENT_NAMES:
            raise RuntimeError(f"Robot {slot} presentation components drifted: {sorted(components)}")
        for name in sorted(components):
            category = "robot_tool" if name == "ToolPresentation" else "robot_link"
            rows.append(component_record(robot, components[name], category, slot))

    found_definitions = set()
    for cell in cells:
        definition = str(cell.get_definition_id())
        if definition not in TARGET_CELL_DEFINITIONS:
            continue
        found_definitions.add(definition)
        components = [component for component in cell.get_components_by_class(unreal.StaticMeshComponent)
                      if component.get_name() == "MainPresentation"]
        if len(components) != 1:
            raise RuntimeError(f"Cell {definition} has {len(components)} MainPresentation components")
        rows.append(component_record(cell, components[0], TARGET_CELL_DEFINITIONS[definition], definition))
    if found_definitions != set(TARGET_CELL_DEFINITIONS):
        raise RuntimeError(f"Authored LOD target cell set drifted: {sorted(found_definitions)}")

    keys = [row["key"] for row in rows]
    if len(rows) != EXPECTED_TARGET_COMPONENT_COUNT or len(keys) != len(set(keys)):
        raise RuntimeError(
            f"Expected {EXPECTED_TARGET_COMPONENT_COUNT} unique renderer target components, found {len(rows)}"
        )
    meshes = {row["mesh_path"] for row in rows}
    if meshes != EXPECTED_UNIQUE_MESHES:
        raise RuntimeError(
            "Robot/tool/vision mesh family drifted: "
            + json.dumps(sorted(meshes), separators=(",", ":"))
        )
    payload["target_components"] = rows
    payload["target_summary"] = {
        "component_count": len(rows),
        "unique_mesh_count": len(meshes),
        "unique_mesh_paths": sorted(meshes),
    }


def configure_view(world, pawn, view_id):
    if not bool(pawn.focus_prototype_process()):
        raise RuntimeError("Management pawn could not focus commissioned process")
    if view_id == "management":
        pawn.set_prototype_zoom_input(-4.0)
    elif view_id != "focus":
        raise RuntimeError("Unknown performance view: " + view_id)

    controller, actual_viewport = game_viewport_size(world)
    cameras = pawn.get_components_by_class(unreal.CameraComponent)
    if controller is None or len(cameras) != 1:
        raise RuntimeError("Possessed controller/camera contract is unavailable")
    if actual_viewport != EXPECTED_VIEWPORT:
        raise RuntimeError(
            "Expected 1920x1080 new-window PIE game viewport, found "
            f"{actual_viewport[0]}x{actual_viewport[1]}"
        )
    payload["views"][view_id] = {
        "id": view_id,
        "viewport": list(actual_viewport),
        "viewport_size_authority": "APlayerController.GetViewportSize",
        "pawn_location_cm": vec(pawn.get_actor_location()),
        "control_rotation_degrees": rot(controller.get_control_rotation()),
        "camera_world_location_cm": vec(cameras[0].get_world_location()),
        "camera_world_rotation_degrees": rot(cameras[0].get_world_rotation()),
        "horizontal_fov_degrees": round(float(cameras[0].get_editor_property("field_of_view")), 3),
        "zoom_distance_cm": round(float(pawn.get_prototype_zoom_distance()), 3),
        "raw_csv": None,
        "primitive_csv_candidates": [],
    }


def begin_primitive_capture(world):
    global primitive_baseline, primitive_started_at_ns
    primitive_baseline = {path.resolve() for path in PRIMITIVE_SOURCE_DIR.glob("PrimitivesDetailed-*.csv")}
    primitive_started_at_ns = time.time_ns()
    unreal.SystemLibrary.execute_console_command(world, "DumpDetailedPrimitives")


def collect_primitive_candidates(view_id):
    candidates = []
    for path in sorted(PRIMITIVE_SOURCE_DIR.glob("PrimitivesDetailed-*.csv"), key=lambda value: value.stat().st_mtime_ns):
        resolved = path.resolve()
        if resolved in primitive_baseline or path.stat().st_mtime_ns < primitive_started_at_ns - 2_000_000_000:
            continue
        target = RAW_DIR / f"{view_id}_primitives_{len(candidates) + 1:02d}.csv"
        shutil.copy2(path, target)
        candidates.append({
            "source": str(path),
            "retained": str(target),
            "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest().upper(),
        })
    if not candidates:
        raise RuntimeError(f"DumpDetailedPrimitives produced no CSV for {view_id}")
    payload["views"][view_id]["primitive_csv_candidates"] = candidates


def begin_profile(world, view_id):
    global profile_path, profile_size, profile_size_changed_at
    profile_name = f"LB_BodyShop_PerfLOD_{STAMP}_{view_id}"
    profile_path = CSV_SOURCE_DIR / f"{profile_name}.csv"
    if profile_path.exists():
        raise RuntimeError(f"Refusing to overwrite exact CSV profile: {profile_path}")
    # Guarantee a directly parseable retained file.  This CVar is process-local
    # and the editor quits without saving any configuration.
    unreal.SystemLibrary.execute_console_command(world, "csv.CompressionMode 0")
    unreal.SystemLibrary.execute_console_command(world, "CsvProfile STARTFILE=" + profile_name)
    unreal.SystemLibrary.execute_console_command(world, f"CsvProfile FRAMES={PROFILE_FRAMES}")
    profile_size = -1
    profile_size_changed_at = time.monotonic()


def profile_is_finalised():
    global profile_size, profile_size_changed_at
    if profile_path is None or not profile_path.exists():
        return False
    size = profile_path.stat().st_size
    if size != profile_size:
        profile_size = size
        profile_size_changed_at = time.monotonic()
        return False
    return size >= 4096 and time.monotonic() - profile_size_changed_at >= PROFILE_STABLE_SECONDS


def retain_profile(view_id):
    target = RAW_DIR / f"{view_id}_performance.csv"
    shutil.copy2(profile_path, target)
    payload["views"][view_id]["raw_csv"] = {
        "source": str(profile_path),
        "retained": str(target),
        "bytes": target.stat().st_size,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest().upper(),
    }


def finish(status, detail=""):
    global tick_handle
    payload["status"] = status
    payload["detail"] = detail
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["map_sha256_after"] = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
    payload["map_hash_unchanged"] = payload["map_sha256_after"] == MAP_SHA_BEFORE
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Saved Body Shop map hash changed during read-only capture")
    if payload["failures"]:
        payload["status"] = "FAIL__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001"
    CAPTURE_RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    try:
        LEVELS.editor_request_end_play()
    finally:
        unreal.SystemLibrary.quit_editor()


def fail(message):
    unreal.log_error("LINE_BOSS_BODY_SHOP_PERFORMANCE_LOD_CAPTURE_FAIL " + message)
    payload["failures"].append(message)
    finish("FAIL__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001", message)


def request_new_window_pie():
    """Start floating PIE through UE's real New Editor Window command path.

    ULevelEditorSubsystem.editor_request_begin_play always supplies the active
    level-editor Slate viewport as DestinationSlateViewport in UE 5.8.  That
    makes -ResX/-ResY irrelevant to the game surface.  Alt+P executes the last
    pinned play command; the runner pins it to PlayMode_InEditorFloating and
    pins NewWindowWidth/NewWindowHeight to 1920x1080 using process-local config
    overrides.
    """
    enable_physical_pixel_dpi_context()
    command_line = payload["engine_command_line"].lower()
    required_tokens = (
        "last-executed-play-mode-type=play-mode-in-editor-floating",
        "new-window-width=1920",
        "new-window-height=1080",
    )
    # Unreal command-line config properties retain their native names.  Strip
    # punctuation so this assertion remains insensitive only to name casing and
    # underscore/camel formatting, never to the requested values or play mode.
    normalised = "".join(character for character in command_line if character.isalnum() or character in "=-")
    normalised = normalised.replace("lastexecutedplaymodetype", "last-executed-play-mode-type")
    normalised = normalised.replace("playmodeineditorfloating", "play-mode-in-editor-floating")
    normalised = normalised.replace("newwindowwidth", "new-window-width")
    normalised = normalised.replace("newwindowheight", "new-window-height")
    missing = [token for token in required_tokens if token not in normalised]
    if missing:
        raise RuntimeError("Missing pinned new-window PIE command-line override(s): " + ", ".join(missing))

    inspector_class = unreal.load_class(
        None,
        "/Script/SlateInspectorToolset.SlateInspectorToolset",
    )
    if inspector_class is None:
        raise RuntimeError("SlateInspectorToolset class is unavailable; cannot request floating PIE")
    inspector = unreal.get_default_object(inspector_class)
    if inspector is None:
        raise RuntimeError("SlateInspectorToolset default object is unavailable")
    pressed = bool(inspector.call_method("PressKey", ("Alt+P",)))
    if not pressed:
        raise RuntimeError("UE Slate command dispatch rejected Alt+P for New Editor Window (PIE)")


def tick(_delta_seconds):
    global tick_number, phase, phase_tick, phase_time, active_view, view_index
    tick_number += 1
    now = time.monotonic()
    if now - started > TIMEOUT_SECONDS:
        fail("Timed out in phase " + phase)
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    try:
        pawns = actors_of(world, unreal.LBBodyShopManagementPawn)
        if phase == "wait_world":
            if now - phase_time < 5.0 or len(pawns) != 1:
                return
            command_line = payload["engine_command_line"].lower()
            if "-nullrhi" in command_line:
                raise RuntimeError("NullRHI is forbidden for the numeric GPU/LOD gate")
            if "-csvgpustats" not in command_line:
                raise RuntimeError("-csvGpuStats is required for numeric GPU timing")
            if int(unreal.SystemLibrary.get_console_variable_int_value("r.GPUCsvStatsEnabled")) != 1:
                raise RuntimeError("r.GPUCsvStatsEnabled is not active")
            payload["capture_contract"]["runtime_cvars"] = {
                "r.GPUCsvStatsEnabled": int(unreal.SystemLibrary.get_console_variable_int_value("r.GPUCsvStatsEnabled")),
                "r.Streaming.PoolSize": int(unreal.SystemLibrary.get_console_variable_int_value("r.Streaming.PoolSize")),
                "r.Streaming.LimitPoolSizeToVRAM": int(unreal.SystemLibrary.get_console_variable_int_value("r.Streaming.LimitPoolSizeToVRAM")),
                "r.ViewDistanceScale": round(float(unreal.SystemLibrary.get_console_variable_float_value("r.ViewDistanceScale")), 4),
                "r.ScreenPercentage": round(float(unreal.SystemLibrary.get_console_variable_float_value("r.ScreenPercentage")), 4),
                "sg.TextureQuality": int(unreal.SystemLibrary.get_console_variable_int_value("sg.TextureQuality")),
            }
            build_target_manifest(world)
            phase = "enforce_viewport"
            phase_tick = tick_number
            phase_time = now
            return

        if phase == "enforce_viewport":
            if len(pawns) != 1:
                raise RuntimeError("Management pawn contract drifted while enforcing viewport size")
            _controller, actual_viewport = game_viewport_size(world)
            if actual_viewport == EXPECTED_VIEWPORT:
                payload["capture_contract"]["viewport_enforcement_result"] = {
                    "status": "exact",
                    "final_game_viewport": list(actual_viewport),
                    "resize_attempts": viewport_resize_attempts,
                }
                active_view = view_order[0]
                configure_view(world, pawns[0], active_view)
                phase = "settle_view"
                phase_tick = tick_number
                return
            if tick_number - phase_tick < VIEWPORT_RESIZE_SETTLE_TICKS:
                return
            if len(viewport_resize_attempts) >= MAX_VIEWPORT_RESIZE_ATTEMPTS:
                raise RuntimeError(
                    "Could not establish exact 1920x1080 floating-PIE game viewport after "
                    f"{MAX_VIEWPORT_RESIZE_ATTEMPTS} native resize attempts; found "
                    f"{actual_viewport[0]}x{actual_viewport[1]}"
                )
            viewport_resize_attempts.append(
                resize_floating_pie_window(actual_viewport)
            )
            phase_tick = tick_number
            return

        if phase == "settle_view":
            if tick_number - phase_tick < VIEW_SETTLE_FRAMES:
                return
            begin_primitive_capture(world)
            phase = "wait_primitives"
            phase_tick = tick_number
            phase_time = now
            return

        if phase == "wait_primitives":
            if now - phase_time < 3.0:
                return
            collect_primitive_candidates(active_view)
            begin_profile(world, active_view)
            phase = "wait_profile"
            phase_tick = tick_number
            return

        if phase == "wait_profile":
            if tick_number - phase_tick < PROFILE_FRAMES + PROFILE_FINALISE_MARGIN_FRAMES:
                return
            if not profile_is_finalised():
                return
            retain_profile(active_view)
            view_index += 1
            if view_index >= len(view_order):
                finish("PASS__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001")
                return
            active_view = view_order[view_index]
            configure_view(world, pawns[0], active_view)
            phase = "settle_view"
            phase_tick = tick_number
    except Exception as exc:
        fail(str(exc))


if not MAP_FILE.exists():
    raise RuntimeError(f"Missing Body Shop map: {MAP_FILE}")
EDITOR_LOD_METADATA = snapshot_editor_lod_metadata()
payload["editor_lod_metadata_snapshot"] = {
    "phase": "pre_pie",
    "source": "live_editor_assets",
    "api": "UStaticMesh.GetNumLODs plus StaticMeshEditorSubsystem.GetLODScreenSizes",
    "mesh_count": len(EDITOR_LOD_METADATA),
    "meshes": EDITOR_LOD_METADATA,
}
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load isolated Body Shop map: {MAP}")
tick_handle = unreal.register_slate_post_tick_callback(tick)
try:
    request_new_window_pie()
except Exception as exc:
    fail(str(exc))
