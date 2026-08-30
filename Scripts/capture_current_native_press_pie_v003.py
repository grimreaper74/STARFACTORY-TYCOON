"""Capture the textured native S02 Deep Draw presentation in a real-RHI PIE run.

This is an immutable v003 evidence script.  It does not alter Content, Config,
maps, or saves: it enters PIE through the ordinary player-builder route, proves
the live six-module S02 mesh/material binding, captures two views, and quits.
"""

from pathlib import Path
import time
import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = ROOT / "Saved/ValidationScreenshots/OneFactory/S02DeepDrawRuntimePresentation_v003"
OUTPUT.mkdir(parents=True, exist_ok=True)
OVERVIEW = OUTPUT / "press_train_a_s02_v003_overview.png"
CLOSE = OUTPUT / "press_train_a_s02_v003_close.png"
MATERIAL_CLOSE = OUTPUT / "press_train_a_s02_v003_material_close.png"
RECEIPT = OUTPUT / "press_train_a_s02_v003_runtime.txt"

MESH_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v003/"
)
MATERIAL_ROOT = MESH_ROOT + "Materials/"

EXPECTED_S02 = {
    "S02DeepDrawPresentation": {
        "mesh": MESH_ROOT + "SM_CA_S02DeepDraw_Static_LOD0_v003."
        "SM_CA_S02DeepDraw_Static_LOD0_v003",
        "materials": (
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_MainGreen_v003."
            "MI_CA_S02DeepDraw_Static_MainGreen_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_Concrete_v003."
            "MI_CA_S02DeepDraw_Static_Concrete_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_DarkSteel_v003."
            "MI_CA_S02DeepDraw_Static_DarkSteel_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_CleanSteel_v003."
            "MI_CA_S02DeepDraw_Static_CleanSteel_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_CharcoalGrey_v003."
            "MI_CA_S02DeepDraw_Static_CharcoalGrey_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_SafetyYellow_v003."
            "MI_CA_S02DeepDraw_Static_SafetyYellow_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_ScreenDark_v003."
            "MI_CA_S02DeepDraw_Static_ScreenDark_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_LampGreen_v003."
            "MI_CA_S02DeepDraw_Static_LampGreen_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_LampAmber_v003."
            "MI_CA_S02DeepDraw_Static_LampAmber_v003",
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Static_LampRed_v003."
            "MI_CA_S02DeepDraw_Static_LampRed_v003",
        ),
    },
    "PressRam_02": {
        "mesh": MESH_ROOT + "SM_CA_S02DeepDraw_Ram_LOD0_v003."
        "SM_CA_S02DeepDraw_Ram_LOD0_v003",
        "materials": (
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Ram_DarkSteel_v003."
            "MI_CA_S02DeepDraw_Ram_DarkSteel_v003",
        ),
    },
    "S02DeepDrawBlankholderPresentation": {
        "mesh": MESH_ROOT + "SM_CA_S02DeepDraw_Blankholder_LOD0_v003."
        "SM_CA_S02DeepDraw_Blankholder_LOD0_v003",
        "materials": (
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Blankholder_CleanSteel_v003."
            "MI_CA_S02DeepDraw_Blankholder_CleanSteel_v003",
        ),
    },
    "S02DeepDrawBolsterPresentation": {
        "mesh": MESH_ROOT + "SM_CA_S02DeepDraw_Bolster_LOD0_v003."
        "SM_CA_S02DeepDraw_Bolster_LOD0_v003",
        "materials": (
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Bolster_CleanSteel_v003."
            "MI_CA_S02DeepDraw_Bolster_CleanSteel_v003",
        ),
    },
    "S02DeepDrawFlywheelPresentation": {
        "mesh": MESH_ROOT + "SM_CA_S02DeepDraw_Flywheel_LOD0_v003."
        "SM_CA_S02DeepDraw_Flywheel_LOD0_v003",
        "materials": (
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_Flywheel_DarkSteel_v003."
            "MI_CA_S02DeepDraw_Flywheel_DarkSteel_v003",
        ),
    },
    "S02DeepDrawSafetyGatePresentation": {
        "mesh": MESH_ROOT + "SM_CA_S02DeepDraw_SafetyGate_LOD0_v003."
        "SM_CA_S02DeepDraw_SafetyGate_LOD0_v003",
        "materials": (
            MATERIAL_ROOT + "MI_CA_S02DeepDraw_SafetyGate_SafetyYellow_v003."
            "MI_CA_S02DeepDraw_SafetyGate_SafetyYellow_v003",
        ),
    },
}

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
started = time.monotonic()
phase = "wait_world"
phase_started = started
task = None
tick_handle = None


def require_one(world, klass, label):
    rows = list(unreal.GameplayStatics.get_all_actors_of_class(world, klass))
    if len(rows) != 1:
        raise RuntimeError(f"Expected one {label}; found {len(rows)}")
    return rows[0]


def get_builder(world):
    rows = [obj for obj in unreal.ObjectIterator(unreal.LBOneFactoryPlayerBuilderSubsystem)
            if obj.get_world() == world]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one player builder; found {len(rows)}")
    return rows[0]


def audit_visible_disallowed_press_content(world):
    disallowed_roots = (
        "/game/lineboss/candidates/pressshop/",
        "/game/lineboss/candidates/presstrains/",
        "/game/lineboss/stations/press/",
        "/game/lineboss/developer/validation/blenderapproved/",
        "/game/lineboss/developer/validation/presstrains/",
    )
    hits = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if actor.hidden:
            continue
        for kind in (unreal.StaticMeshComponent,
                     unreal.InstancedStaticMeshComponent,
                     unreal.HierarchicalInstancedStaticMeshComponent):
            for component in actor.get_components_by_class(kind):
                mesh = component.get_editor_property("static_mesh")
                path = str(mesh.get_path_name()).lower() if mesh else ""
                if (path and any(path.startswith(root) for root in disallowed_roots)
                        and component.is_visible() and not component.hidden_in_game):
                    hits.append(f"{actor.get_name()}/{component.get_name()}={path}")
    return sorted(set(hits))


def audit_s02_runtime_modules(press):
    observed = []
    components = {
        str(component.get_name()): component
        for component in press.get_components_by_class(unreal.StaticMeshComponent)
    }
    missing = sorted(set(EXPECTED_S02) - set(components))
    if missing:
        raise RuntimeError("Missing live v003 S02 components: " + ", ".join(missing))
    for name, expected in EXPECTED_S02.items():
        component = components[name]
        mesh = component.get_editor_property("static_mesh")
        mesh_path = str(mesh.get_path_name()) if mesh else "none"
        if mesh_path != expected["mesh"]:
            raise RuntimeError(f"S02 v003 mesh mismatch: {name}={mesh_path}")
        if not component.is_visible() or component.hidden_in_game:
            raise RuntimeError(
                f"S02 v003 visibility mismatch: {name}; "
                f"visible={component.is_visible()} hidden={component.hidden_in_game}")
        actual_count = component.get_num_materials()
        expected_materials = expected["materials"]
        if actual_count != len(expected_materials):
            raise RuntimeError(
                f"S02 v003 material-slot count mismatch: {name}="
                f"{actual_count}, expected {len(expected_materials)}")
        actual_materials = []
        for slot, expected_path in enumerate(expected_materials):
            material = component.get_material(slot)
            material_path = str(material.get_path_name()) if material else "none"
            if material_path != expected_path:
                raise RuntimeError(
                    f"S02 v003 material mismatch: {name}[{slot}]={material_path}")
            actual_materials.append(material_path)
        location = component.get_world_transform().translation
        observed.append(
            f"{name}=({location.x:.1f},{location.y:.1f},{location.z:.1f});"
            f"mesh={mesh_path};materials={' | '.join(actual_materials)}")
    return observed


def finish(status):
    global tick_handle
    RECEIPT.write_text(status + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started, task
    try:
        now = time.monotonic()
        if now - started > 120:
            raise RuntimeError("Timed out while capturing native textured S02 PIE")
        world = WORLDS.get_game_world()
        if world is None:
            return
        if phase == "wait_world":
            if now - phase_started < 5:
                return
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            hud = require_one(world, unreal.LBControlRoomHUD, "control-room HUD")
            builder = get_builder(world)
            hud.open_factory_build()
            accepted = hud.activate_management_action(0)
            reason = str(builder.get_last_action_reason())
            if not accepted and "PRESENTATIONS LIVE" not in reason:
                raise RuntimeError("New Factory action rejected: " + reason)
            if not pawn.set_automation_camera(
                    unreal.Vector(-14500.0, 7000.0, 0.0), -50.0, 30000.0):
                raise RuntimeError("Could not frame the textured native press overview")
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(OVERVIEW), force_game_view=False)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected S02 v003 overview capture")
            phase = "wait_overview"
            phase_started = now
            return
        if phase == "wait_overview":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not OVERVIEW.is_file() or OVERVIEW.stat().st_size < 4096:
                raise RuntimeError("S02 v003 overview screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            if not pawn.set_automation_camera(
                    unreal.Vector(-9000.0, 8000.0, 0.0), -50.0, 16000.0):
                raise RuntimeError("Could not frame textured S02 close view")
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(CLOSE), force_game_view=False)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected S02 v003 close capture")
            phase = "wait_close"
            phase_started = now
            return
        if phase == "wait_close":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not CLOSE.is_file() or CLOSE.stat().st_size < 4096:
                raise RuntimeError("S02 v003 close screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            if not pawn.set_automation_camera(
                    unreal.Vector(-9000.0, 8000.0, 0.0), -50.0, 6500.0):
                raise RuntimeError("Could not frame S02 material close-up")
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(MATERIAL_CLOSE), force_game_view=False)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected S02 v003 material close capture")
            phase = "wait_material_close"
            phase_started = now
            return
        if phase == "wait_material_close":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not MATERIAL_CLOSE.is_file() or MATERIAL_CLOSE.stat().st_size < 4096:
                raise RuntimeError("S02 v003 material close screenshot was not written")
            press = require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                                "native press presentation")
            tooling = require_one(world, unreal.LBOneFactoryPressToolingSupportActor,
                                  "native die tooling")
            feed = require_one(world, unreal.LBOneFactoryPressFeedPresentationActor,
                               "native upstream presentation")
            disallowed = audit_visible_disallowed_press_content(world)
            if disallowed:
                raise RuntimeError(
                    "Visible disallowed legacy/candidate press content: "
                    + " | ".join(disallowed))
            modules = audit_s02_runtime_modules(press)
            finish(
                "PASS textured S02 v003 native press PIE capture; "
                f"animated_mechanisms={press.get_animated_mechanism_count()}; "
                f"stored_die_sets={tooling.get_stored_die_set_count()}; "
                f"upstream_configured={feed.is_configured()}"
                f"\ns02_v003_modules={' || '.join(modules)}"
                "\ndisallowed_visible_press_content=none"
            )
    except Exception as exc:
        unreal.log_error("S02_V003_NATIVE_PRESS_CAPTURE_FAIL " + str(exc))
        finish("FAIL " + str(exc))


try:
    for screenshot in (OVERVIEW, CLOSE, MATERIAL_CLOSE):
        if screenshot.exists():
            screenshot.unlink()
    if not LEVELS.load_level(MAP):
        raise RuntimeError("Could not load the OneFactory map")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as exc:
    unreal.log_error("S02_V003_NATIVE_PRESS_CAPTURE_START_FAIL " + str(exc))
    finish("FAIL " + str(exc))
