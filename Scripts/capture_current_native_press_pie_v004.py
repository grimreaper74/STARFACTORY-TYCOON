"""Real-RHI PIE evidence for S02 plus the native S03-S06 StagePack actor pass.

This is a new, immutable evidence lane: it never saves Content, Config, or a
map.  It uses the ordinary OneFactory builder route, verifies live component
closure, captures overview/operator/service views, and writes only beneath its
own Saved/ValidationScreenshots folder.
"""

import json
from pathlib import Path
import time

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = ROOT / "Saved/ValidationScreenshots/OneFactory/NativePressTrainStagePack_v004"
OUTPUT.mkdir(parents=True, exist_ok=True)
OVERVIEW = OUTPUT / "press_train_native_v004_retry1_overview.png"
OPERATOR = OUTPUT / "press_train_native_v004_retry1_operator_side.png"
SERVICE = OUTPUT / "press_train_native_v004_retry1_service_side.png"
RECEIPT = OUTPUT / "press_train_native_v004_runtime_retry1.json"

S02_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v003/"
)
STAGE_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v003/"
)
STAGE_MATERIAL_ROOT = STAGE_ROOT + "Materials/"

EXPECTED_S02_MESHES = {
    "S02DeepDrawPresentation": S02_ROOT + "SM_CA_S02DeepDraw_Static_LOD0_v003."
    "SM_CA_S02DeepDraw_Static_LOD0_v003",
    "PressRam_02": S02_ROOT + "SM_CA_S02DeepDraw_Ram_LOD0_v003."
    "SM_CA_S02DeepDraw_Ram_LOD0_v003",
    "S02DeepDrawBlankholderPresentation": S02_ROOT
    + "SM_CA_S02DeepDraw_Blankholder_LOD0_v003.SM_CA_S02DeepDraw_Blankholder_LOD0_v003",
    "S02DeepDrawBolsterPresentation": S02_ROOT
    + "SM_CA_S02DeepDraw_Bolster_LOD0_v003.SM_CA_S02DeepDraw_Bolster_LOD0_v003",
    "S02DeepDrawFlywheelPresentation": S02_ROOT
    + "SM_CA_S02DeepDraw_Flywheel_LOD0_v003.SM_CA_S02DeepDraw_Flywheel_LOD0_v003",
    "S02DeepDrawSafetyGatePresentation": S02_ROOT
    + "SM_CA_S02DeepDraw_SafetyGate_LOD0_v003.SM_CA_S02DeepDraw_SafetyGate_LOD0_v003",
}

EXPECTED_STAGE_MESHES = {
    "S03StagePackFramePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S03_Frame_Form_LOD0_v001.SM_CA_MW_PT_S03_Frame_Form_LOD0_v001",
    "S03StagePackCuePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S03_Cue_SecondaryForm_LOD0_v001.SM_CA_MW_PT_S03_Cue_SecondaryForm_LOD0_v001",
    "S04StagePackFramePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S04_Frame_Trim_LOD0_v001.SM_CA_MW_PT_S04_Frame_Trim_LOD0_v001",
    "S04StagePackCuePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S04_Cue_TrimScrap_LOD0_v001.SM_CA_MW_PT_S04_Cue_TrimScrap_LOD0_v001",
    "S05StagePackFramePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S05_Frame_Pierce_LOD0_v001.SM_CA_MW_PT_S05_Frame_Pierce_LOD0_v001",
    "S05StagePackCuePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S05_Cue_PierceSlug_LOD0_v001.SM_CA_MW_PT_S05_Cue_PierceSlug_LOD0_v001",
    "S06StagePackFramePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S06_Frame_Flange_LOD0_v001.SM_CA_MW_PT_S06_Frame_Flange_LOD0_v001",
    "S06StagePackCuePresentation": STAGE_ROOT
    + "Meshes/SM_CA_MW_PT_S06_Cue_RestrikeQuality_LOD0_v001.SM_CA_MW_PT_S06_Cue_RestrikeQuality_LOD0_v001",
}

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
started = time.monotonic()
phase = "wait_world"
phase_started = started
task = None
tick_handle = None


def asset_path(asset):
    return str(asset.get_path_name()) if asset else "none"


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
                path = asset_path(mesh).lower()
                if (path and any(path.startswith(root) for root in disallowed_roots)
                        and component.is_visible() and not component.hidden_in_game):
                    hits.append(f"{actor.get_name()}/{component.get_name()}={path}")
    return sorted(set(hits))


def live_static_components(press):
    return {
        str(component.get_name()): component
        for component in press.get_components_by_class(unreal.StaticMeshComponent)
    }


def vector_tuple(value):
    return (round(value.x, 3), round(value.y, 3), round(value.z, 3))


def audit_s02(components):
    observed = {}
    missing = sorted(set(EXPECTED_S02_MESHES) - set(components))
    if missing:
        raise RuntimeError("Missing live v003 S02 components: " + ", ".join(missing))
    for name, expected_mesh in EXPECTED_S02_MESHES.items():
        component = components[name]
        actual_mesh = asset_path(component.get_editor_property("static_mesh"))
        if actual_mesh != expected_mesh:
            raise RuntimeError(f"S02 v003 mesh mismatch: {name}={actual_mesh}")
        if not component.is_visible() or component.hidden_in_game:
            raise RuntimeError(f"S02 v003 visibility mismatch: {name}")
        observed[name] = {
            "mesh": actual_mesh,
            "material_count": component.get_num_materials(),
            "world_location_cm": vector_tuple(component.get_world_transform().translation),
        }
    return observed


def audit_stagepack(press, components):
    missing = sorted(set(EXPECTED_STAGE_MESHES) - set(components))
    if missing:
        raise RuntimeError("Missing live StagePack components: " + ", ".join(missing))
    observed = {}
    frame_locations = []
    for name, expected_mesh in EXPECTED_STAGE_MESHES.items():
        component = components[name]
        mesh = component.get_editor_property("static_mesh")
        actual_mesh = asset_path(mesh)
        if actual_mesh != expected_mesh:
            raise RuntimeError(f"StagePack mesh mismatch: {name}={actual_mesh}")
        if not component.is_visible() or component.hidden_in_game:
            raise RuntimeError(f"StagePack visibility mismatch: {name}")
        slots = list(mesh.static_materials)
        if component.get_num_materials() != len(slots):
            raise RuntimeError(f"StagePack material count mismatch: {name}")
        materials = []
        for index, slot in enumerate(slots):
            semantic = str(slot.material_slot_name)
            if not semantic.startswith("CA_MW_"):
                raise RuntimeError(f"StagePack semantic slot malformed: {name}[{index}]={semantic}")
            family = semantic.removeprefix("CA_MW_")
            expected_material = (STAGE_MATERIAL_ROOT + f"MI_CA_MW_PT_{family}_v001."
                                 f"MI_CA_MW_PT_{family}_v001")
            actual_material = asset_path(component.get_material(index))
            if actual_material != expected_material:
                raise RuntimeError(
                    f"StagePack material mismatch: {name}[{index}]={actual_material}")
            materials.append(actual_material)
        transform = component.get_world_transform()
        if any(abs(value - 1.0) > 0.001 for value in vector_tuple(transform.scale3d)):
            raise RuntimeError(f"StagePack scale is not unit: {name}")
        observed[name] = {
            "mesh": actual_mesh,
            "materials": materials,
            "world_location_cm": vector_tuple(transform.translation),
            "world_rotation": [round(transform.rotation.x, 5), round(transform.rotation.y, 5),
                               round(transform.rotation.z, 5), round(transform.rotation.w, 5)],
            "world_scale": vector_tuple(transform.scale3d),
        }
        if name.endswith("FramePresentation"):
            frame_locations.append(transform.translation)
    for station in ("S03", "S04", "S05", "S06"):
        frame = components[f"{station}StagePackFramePresentation"].get_world_transform()
        cue = components[f"{station}StagePackCuePresentation"].get_world_transform()
        if (frame.translation - cue.translation).length() > 0.01:
            raise RuntimeError(f"{station} StagePack frame/cue roots do not share one station transform")
        if not frame.rotation.equals(cue.rotation, 0.00001):
            raise RuntimeError(f"{station} StagePack frame/cue rotations differ")
    for current, following in zip(frame_locations, frame_locations[1:]):
        distance = (following - current).length()
        if abs(distance - 1450.0) > 0.1:
            raise RuntimeError(f"StagePack train pitch={distance:.3f} cm, expected 1450")
    batches = {
        str(component.get_name()): component
        for component in press.get_components_by_class(unreal.InstancedStaticMeshComponent)
    }
    # S01 and S07 retain their generic press bodies.  S07 also intentionally
    # contributes its narrow inspection gantry through NativeStationCrowns, so
    # its batch count is three rather than the two generic press crowns.
    expected_batch_counts = {
        "NativeStationBases": 2,
        "NativeStationCrowns": 3,
    }
    for batch_name, expected_count in expected_batch_counts.items():
        component = batches.get(batch_name)
        count = component.get_instance_count() if component else -1
        if count != expected_count:
            raise RuntimeError(
                f"Generic {batch_name} count={count}, expected {expected_count} after StagePack replacement")
    return observed


def finish(result):
    global tick_handle
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def begin_screenshot(world, pawn, position, pitch, distance, destination, next_phase):
    global phase, phase_started, task
    if not pawn.set_automation_camera(position, pitch, distance):
        raise RuntimeError(f"Could not frame {next_phase} camera")
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(destination), force_game_view=False)
    if not task.is_valid_task():
        raise RuntimeError(f"Unreal rejected {next_phase} screenshot")
    phase = next_phase
    phase_started = time.monotonic()


def wait_screenshot(destination):
    return task is not None and task.is_task_done() and destination.is_file() and destination.stat().st_size >= 4096


def tick(_delta):
    global phase, phase_started
    try:
        now = time.monotonic()
        if now - started > 150:
            raise RuntimeError("Timed out while capturing native StagePack PIE")
        world = WORLDS.get_game_world()
        if world is None:
            return
        if phase == "wait_world":
            if now - phase_started < 5.0:
                return
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            hud = require_one(world, unreal.LBControlRoomHUD, "control-room HUD")
            builder = get_builder(world)
            hud.open_factory_build()
            accepted = hud.activate_management_action(0)
            reason = str(builder.get_last_action_reason())
            if not accepted and "PRESENTATIONS LIVE" not in reason:
                raise RuntimeError("New Factory action rejected: " + reason)
            begin_screenshot(world, pawn, unreal.Vector(-14500.0, 7000.0, 0.0),
                             -50.0, 30000.0, OVERVIEW, "wait_overview")
            return
        if phase == "wait_overview":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not wait_screenshot(OVERVIEW):
                raise RuntimeError("Overview screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            begin_screenshot(world, pawn, unreal.Vector(-10500.0, 7200.0, 0.0),
                             -44.0, 21000.0, OPERATOR, "wait_operator")
            return
        if phase == "wait_operator":
            if now -phase_started < 1.5 or not task.is_task_done():
                return
            if not wait_screenshot(OPERATOR):
                raise RuntimeError("Operator-side screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            begin_screenshot(world, pawn, unreal.Vector(10500.0, 7200.0, 0.0),
                             -44.0, 21000.0, SERVICE, "wait_service")
            return
        if phase == "wait_service":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not wait_screenshot(SERVICE):
                raise RuntimeError("Service-side screenshot was not written")
            press = require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                                "native press presentation")
            components = live_static_components(press)
            disallowed = audit_visible_disallowed_press_content(world)
            if disallowed:
                raise RuntimeError("Visible disallowed press content: " + " | ".join(disallowed))
            result = {
                "$schema": "lineboss/evidence/onefactory/native-press-train-stagepack-v004/v1",
                "status": "PASS__NATIVE_S02_AND_S03S06_STAGEPACK_PIE",
                "screenshots": [str(OVERVIEW), str(OPERATOR), str(SERVICE)],
                "animated_mechanisms": press.get_animated_mechanism_count(),
                "s02_v003": audit_s02(components),
                "stagepack_v003": audit_stagepack(press, components),
                "disallowed_visible_press_content": [],
                "content_writes": [],
                "map_loaded_or_saved": [],
            }
            finish(result)
    except Exception as exc:
        unreal.log_error("NATIVE_PRESS_STAGEPACK_V004_CAPTURE_FAIL " + str(exc))
        finish({
            "$schema": "lineboss/evidence/onefactory/native-press-train-stagepack-v004/v1",
            "status": "FAIL__NATIVE_S02_AND_S03S06_STAGEPACK_PIE",
            "error": str(exc),
            "content_writes": [],
            "map_loaded_or_saved": [],
        })


try:
    for screenshot in (OVERVIEW, OPERATOR, SERVICE):
        if screenshot.exists():
            screenshot.unlink()
    if not LEVELS.load_level(MAP):
        raise RuntimeError("Could not load the OneFactory map")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as exc:
    unreal.log_error("NATIVE_PRESS_STAGEPACK_V004_CAPTURE_START_FAIL " + str(exc))
    finish({
        "$schema": "lineboss/evidence/onefactory/native-press-train-stagepack-v004/v1",
        "status": "FAIL__NATIVE_S02_AND_S03S06_STAGEPACK_PIE",
        "error": str(exc),
        "content_writes": [],
        "map_loaded_or_saved": [],
    })
