"""Capture the current native Press Train A in a disposable real-RHI PIE run.

This deliberately does not alter Content, Config, maps or saves.  It creates the
factory through the normal UMG builder route in PIE, captures the current runtime
press scene, then closes the editor session.
"""

from pathlib import Path
import time
import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = ROOT / "Saved/ValidationScreenshots/OneFactory/S02DeepDrawRuntimePresentation_v002"
OUTPUT.mkdir(parents=True, exist_ok=True)
SHOT = OUTPUT / "press_train_a_s02_v002_overview.png"
CLOSE_SHOT = OUTPUT / "press_train_a_s02_v002_close.png"
RECEIPT = OUTPUT / "press_train_a_s02_v002_runtime.txt"

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


def audit_legacy_press_runtime(world):
    """Return exact live actor names carrying legacy press/candidate content.

    Asset-registry warnings are not proof that a candidate mesh is displayed. This
    runs in the actual PIE world, and checks actor classes plus every mesh-bearing
    component so the visual cleanup decision is based on runtime evidence.
    """
    hits = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        actor_path = str(actor.get_class().get_path_name()).lower()
        actor_name = str(actor.get_name())
        component_paths = []
        for component_type in (unreal.StaticMeshComponent,
                               unreal.InstancedStaticMeshComponent,
                               unreal.HierarchicalInstancedStaticMeshComponent):
            for component in actor.get_components_by_class(component_type):
                mesh = component.get_editor_property("static_mesh")
                if mesh:
                    component_paths.append(str(mesh.get_path_name()).lower())
        suspect = ("lbpresstraina" in actor_path
                   or "candidates/pressshop" in actor_path
                   or any("/candidates/pressshop/" in path for path in component_paths))
        if suspect:
            hits.append(actor_name + "=" + actor_path)
    return sorted(set(hits))


def audit_detailed_aggregate_runtime(world):
    hits = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            if mesh and "sm_onefactorydetailedpresspresentation" in str(mesh.get_path_name()).lower():
                hits.append(str(actor.get_name()))
    return sorted(set(hits))


def audit_s02_runtime_modules(press):
    """Prove the live actor resolves the six approved v002 runtime modules."""
    expected = {
        "S02DeepDrawPresentation": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v002/SM_CA_S02DeepDraw_Static_LOD0_v002.SM_CA_S02DeepDraw_Static_LOD0_v002",
        "PressRam_02": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v002/SM_CA_S02DeepDraw_Ram_LOD0_v002.SM_CA_S02DeepDraw_Ram_LOD0_v002",
        "S02DeepDrawBlankholderPresentation": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v002/SM_CA_S02DeepDraw_Blankholder_LOD0_v002.SM_CA_S02DeepDraw_Blankholder_LOD0_v002",
        "S02DeepDrawBolsterPresentation": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v002/SM_CA_S02DeepDraw_Bolster_LOD0_v002.SM_CA_S02DeepDraw_Bolster_LOD0_v002",
        "S02DeepDrawFlywheelPresentation": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v002/SM_CA_S02DeepDraw_Flywheel_LOD0_v002.SM_CA_S02DeepDraw_Flywheel_LOD0_v002",
        "S02DeepDrawSafetyGatePresentation": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v002/SM_CA_S02DeepDraw_SafetyGate_LOD0_v002.SM_CA_S02DeepDraw_SafetyGate_LOD0_v002",
    }
    observed = {}
    for component in press.get_components_by_class(unreal.StaticMeshComponent):
        name = str(component.get_name())
        if name not in expected:
            continue
        mesh = component.get_editor_property("static_mesh")
        path = str(mesh.get_path_name()) if mesh else "none"
        if path != expected[name]:
            raise RuntimeError(f"S02 runtime module mismatch: {name}={path}")
        if not component.visible or component.hidden_in_game:
            raise RuntimeError(
                f"S02 runtime module visibility state is invalid: {name} "
                f"visible={component.visible} hidden_in_game={component.hidden_in_game}")
        transform = component.get_world_transform()
        location = transform.translation
        observed[name] = (f"{name}=({location.x:.1f},{location.y:.1f},"
                          f"{location.z:.1f});{path}")
    if set(observed) != set(expected):
        missing = sorted(set(expected) - set(observed))
        raise RuntimeError("Missing live S02 v002 runtime modules: " + ", ".join(missing))
    return [observed[name] for name in sorted(observed)]


def audit_visible_press_like_runtime(world):
    """Records the actual owners of any remaining press-looking presentation.

    This deliberately looks beyond the retired Candidates folder: older map
    dressing used generic AssemblyLineBox meshes, which can still resemble a
    press train even though their asset paths do not say PressShop.
    """
    tokens = ("press", "assemblylinebox", "assemblyline01", "destack",
              "meshy", "industrialrobot")
    hits = []
    component_types = (unreal.StaticMeshComponent,
                       unreal.InstancedStaticMeshComponent,
                       unreal.HierarchicalInstancedStaticMeshComponent)
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for component_type in component_types:
            for component in actor.get_components_by_class(component_type):
                mesh = component.get_editor_property("static_mesh")
                mesh_path = str(mesh.get_path_name()).lower() if mesh else ""
                if not mesh_path or not any(token in mesh_path for token in tokens):
                    continue
                if hasattr(component, "is_visible") and not component.is_visible():
                    continue
                instances = ""
                if hasattr(component, "get_instance_count"):
                    instances = f" instances={component.get_instance_count()}"
                hits.append(f"{actor.get_name()}[{actor.get_class().get_name()}]"
                            f"/{component.get_name()}={mesh_path}{instances}")
    return sorted(set(hits))


def hide_retired_map_press_meshes(world):
    """Temporary capture assertion mirroring the runtime retirement policy."""
    roots = ("/game/lineboss/candidates/pressshop/",
             "/game/lineboss/stations/press/",
             "/game/lineboss/candidates/presstrains/",
             "/game/lineboss/developer/validation/blenderapproved",
             "/game/lineboss/developer/validation/presstrains/")
    hidden = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            path = str(mesh.get_path_name()).lower() if mesh else ""
            if path and any(path.startswith(root) for root in roots):
                actor.set_actor_hidden_in_game(True)
                hidden += 1
                break
    return hidden


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
        if now - started > 90:
            raise RuntimeError("Timed out while capturing current native press PIE")
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
            action_accepted = hud.activate_management_action(0)
            action_reason = str(builder.get_last_action_reason())
            # The player builder may have already created the native
            # presentations during its first HUD refresh.  That is a valid
            # populated factory state, not a rejection of the capture route.
            if not action_accepted and "PRESENTATIONS LIVE" not in action_reason:
                raise RuntimeError("New Factory action rejected: " + action_reason)
            hidden_retired_press_actors = hide_retired_map_press_meshes(world)
            # The overview deliberately includes S01-S07 plus upstream staging.
            if not pawn.set_automation_camera(
                    unreal.Vector(-14500.0, 7000.0, 0.0), -50.0, 30000.0):
                raise RuntimeError("Could not frame the populated press overview")
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(SHOT), force_game_view=False)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected native press screenshot task")
            phase = "wait_screenshot"
            phase_started = now
            return
        if phase == "wait_screenshot":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not SHOT.is_file() or SHOT.stat().st_size < 4096:
                raise RuntimeError("Native press screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            if not pawn.set_automation_camera(
                    # The press train lives at the S01-S07 authority datum. The
                    # former inspection-centric target aimed at empty reserved
                    # floor, so this deliberately frames the actual train centre.
                    unreal.Vector(-9000.0, 8000.0, 0.0), -50.0, 16000.0):
                raise RuntimeError("Could not frame the native Press Train A close view")
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(CLOSE_SHOT), force_game_view=False)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected native press close screenshot task")
            phase = "wait_close_screenshot"
            phase_started = now
            return
        if phase == "wait_close_screenshot":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not CLOSE_SHOT.is_file() or CLOSE_SHOT.stat().st_size < 4096:
                raise RuntimeError("Native press close screenshot was not written")
            press = require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                                "native press presentation")
            tooling = require_one(world, unreal.LBOneFactoryPressToolingSupportActor,
                                  "native die tooling")
            feed = require_one(world, unreal.LBOneFactoryPressFeedPresentationActor,
                                "native upstream presentation")
            legacy_hits = audit_legacy_press_runtime(world)
            detailed_hits = audit_detailed_aggregate_runtime(world)
            press_like_hits = audit_visible_press_like_runtime(world)
            native_positions = []
            for component in press.get_components_by_class(unreal.ActorComponent):
                name = str(component.get_name())
                if isinstance(component, unreal.InstancedStaticMeshComponent):
                    count = component.get_instance_count()
                    if count:
                        transform = component.get_instance_transform(0, True)
                        location = transform.translation
                        mesh = component.get_editor_property("static_mesh")
                        mesh_name = str(mesh.get_path_name()) if mesh else "none"
                        native_positions.append(
                            f"{name}[{count};visible={component.is_visible()}]"
                            f"=({location.x:.0f},{location.y:.0f},{location.z:.0f});{mesh_name}")
                elif any(token in name for token in ("Transfer", "PressRam", "Destack", "S02DeepDraw")):
                    native_positions.append(name)
            s02_modules = audit_s02_runtime_modules(press)
            finish(
                "PASS native current press PIE capture; "
                f"animated_mechanisms={press.get_animated_mechanism_count()}; "
                f"stored_die_sets={tooling.get_stored_die_set_count()}; "
                f"upstream_configured={feed.is_configured()}; "
                f"legacy_press_runtime_hits={len(legacy_hits)}; "
                f"legacy_press_runtime_actors={' | '.join(legacy_hits) or 'none'}; "
                f"detailed_aggregate_runtime_actors={' | '.join(detailed_hits) or 'none'}"
                f"\ns02_runtime_modules={' | '.join(s02_modules)}"
                f"\nnative_component_positions={' | '.join(native_positions) or 'none'}"
                f"\nvisible_press_like_runtime={' | '.join(press_like_hits) or 'none'}"
            )
    except Exception as exc:
        unreal.log_error("CURRENT_NATIVE_PRESS_CAPTURE_FAIL " + str(exc))
        finish("FAIL " + str(exc))


try:
    for screenshot in (SHOT, CLOSE_SHOT):
        if screenshot.exists():
            screenshot.unlink()
    if not LEVELS.load_level(MAP):
        raise RuntimeError("Could not load the OneFactory map")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as exc:
    unreal.log_error("CURRENT_NATIVE_PRESS_CAPTURE_START_FAIL " + str(exc))
    finish("FAIL " + str(exc))
