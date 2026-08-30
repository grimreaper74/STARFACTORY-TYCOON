"""Real-RHI PIE evidence for the native S02/S03-S06 press train plus MaterialFlow v002.

This is a non-destructive capture lane.  It opens the existing OneFactory map,
uses the ordinary builder route, never saves a map or Content, and writes only
its screenshots and receipt beneath Saved/ValidationScreenshots.
"""

import json
from pathlib import Path
import time

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = ROOT / "Saved/ValidationScreenshots/OneFactory/NativePressTrainMaterialFlow_v005"
OUTPUT.mkdir(parents=True, exist_ok=True)
OVERVIEW = OUTPUT / "press_train_native_v005_overview.png"
OPERATOR = OUTPUT / "press_train_native_v005_operator_side.png"
SERVICE = OUTPUT / "press_train_native_v005_service_side.png"
RECEIPT = OUTPUT / "press_train_native_v005_runtime.json"

S02_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v003/"
)
STAGE_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v003/"
)
STAGE_MATERIAL_ROOT = STAGE_ROOT + "Materials/"
FLOW_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "MaterialFlowPack_v002/"
)
FLOW_MATERIAL_ROOT = FLOW_ROOT + "Materials/"

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

EXPECTED_FLOW_MESHES = {
    "S01CoilCartMover": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S01CoilCart_v001.SM_CA_MW_PT_S01CoilCart_v001",
    "S01CoilRackPresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S01CoilRack_v001.SM_CA_MW_PT_S01CoilRack_v001",
    "S01DecoilerBasePresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S01DecoilerBase_v001.SM_CA_MW_PT_S01DecoilerBase_v001",
    "S01DecoilerSpindleMover": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S01DecoilerSpindle_v001.SM_CA_MW_PT_S01DecoilerSpindle_v001",
    "S01StraightenerFeedPresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S01StraightenerFeed_v001.SM_CA_MW_PT_S01StraightenerFeed_v001",
    "S01FeedBridgePresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S01FeedBridge_v001.SM_CA_MW_PT_S01FeedBridge_v001",
    "S07ExitConveyorBeltPresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001.SM_CA_MW_PT_S07ExitConveyorBelt_v001",
    "S07ExitConveyorFramePresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001.SM_CA_MW_PT_S07ExitConveyorFrame_v001",
    "S07InspectionCellPresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S07InspectionCell_v001.SM_CA_MW_PT_S07InspectionCell_v001",
    "S07OutboundDunnagePresentation": FLOW_ROOT
    + "Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001.SM_CA_MW_PT_S07OutboundDunnage_v001",
}

EXPECTED_FLOW_BOUNDS = {
    "S01CoilCartMover": (200.0, 161.0, 68.503),
    "S01CoilRackPresentation": (327.0, 480.0, 168.0),
    "S01DecoilerBasePresentation": (279.5, 177.0, 225.508),
    "S01DecoilerSpindleMover": (161.0, 144.0, 144.0),
    "S01StraightenerFeedPresentation": (338.0, 304.0, 167.5),
    "S01FeedBridgePresentation": (110.0, 428.0, 135.0),
    "S07ExitConveyorBeltPresentation": (150.0, 460.0, 28.0),
    "S07ExitConveyorFramePresentation": (250.0, 505.0, 98.0),
    "S07InspectionCellPresentation": (440.0, 238.0, 241.0),
    "S07OutboundDunnagePresentation": (392.5, 330.5, 149.099),
}

SHARED_MATERIALS = {
    "CA_MW_CairnwellGreen", "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
    "CA_MW_SafetyYellow", "CA_MW_WorkedSteel", "CA_MW_InspectionGlass",
    "CA_MW_TrainAAccent", "CA_MW_StatusGreen", "CA_MW_StatusAmber",
}
FLOW_MATERIALS = {
    "CA_MW_DarkRubber", "CA_MW_GalvanizedCoil", "CA_MW_StampedPanel",
    "CA_MW_TaskLightGlass",
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


def vector_tuple(value):
    return (round(value.x, 3), round(value.y, 3), round(value.z, 3))


def close_tuple(actual, expected, tolerance=0.5):
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def live_static_components(press):
    return {str(component.get_name()): component
            for component in press.get_components_by_class(unreal.StaticMeshComponent)}


def expected_flow_material(slot_name):
    if slot_name in SHARED_MATERIALS:
        family = slot_name.removeprefix("CA_MW_")
        return STAGE_MATERIAL_ROOT + f"MI_CA_MW_PT_{family}_v001.MI_CA_MW_PT_{family}_v001"
    if slot_name in FLOW_MATERIALS:
        family = slot_name.removeprefix("CA_MW_")
        return FLOW_MATERIAL_ROOT + f"MI_CA_MW_PT_{family}_v001.MI_CA_MW_PT_{family}_v001"
    raise RuntimeError(f"MaterialFlow has an unapproved semantic slot: {slot_name}")


def audit_s02(components):
    rows = {}
    for name, expected_mesh in EXPECTED_S02_MESHES.items():
        component = components.get(name)
        if component is None:
            raise RuntimeError(f"Missing live S02 component: {name}")
        actual_mesh = asset_path(component.get_editor_property("static_mesh"))
        if actual_mesh != expected_mesh or not component.is_visible() or component.hidden_in_game:
            raise RuntimeError(f"S02 v003 binding or visibility mismatch: {name}")
        rows[name] = {"mesh": actual_mesh,
                      "world_location_cm": vector_tuple(component.get_world_transform().translation)}
    return rows


def audit_stagepack(press, components):
    rows = {}
    for name, expected_mesh in EXPECTED_STAGE_MESHES.items():
        component = components.get(name)
        if component is None:
            raise RuntimeError(f"Missing live StagePack component: {name}")
        mesh = component.get_editor_property("static_mesh")
        if asset_path(mesh) != expected_mesh or not component.is_visible() or component.hidden_in_game:
            raise RuntimeError(f"StagePack binding or visibility mismatch: {name}")
        rows[name] = {"mesh": asset_path(mesh),
                      "world_location_cm": vector_tuple(component.get_world_transform().translation)}
    for station in ("S03", "S04", "S05", "S06"):
        frame = components[f"{station}StagePackFramePresentation"].get_world_transform()
        cue = components[f"{station}StagePackCuePresentation"].get_world_transform()
        if (frame.translation - cue.translation).length() > 0.01:
            raise RuntimeError(f"{station} StagePack frame/cue roots do not match")
    batches = {str(component.get_name()): component
               for component in press.get_components_by_class(unreal.InstancedStaticMeshComponent)}
    for name in ("NativeStationBases", "NativeStationCrowns"):
        component = batches.get(name)
        if component is None or component.get_instance_count() != 0:
            count = component.get_instance_count() if component else -1
            raise RuntimeError(f"Generic endpoint overlap remains: {name}={count}, expected 0")
    return rows


def audit_materialflow(components):
    missing = sorted(set(EXPECTED_FLOW_MESHES) - set(components))
    if missing:
        raise RuntimeError("Missing MaterialFlow components: " + ", ".join(missing))
    rows = {}
    s01_root = (-8990.75, 6017.5, 0.0)
    s07_root = (-8990.75, 14717.5, 0.0)
    parked = {
        "S01CoilCartMover": (-8770.75, 6447.5, 32.0),
        "S01DecoilerSpindleMover": (-9010.75, 6137.5, 115.0),
    }
    for name, expected_mesh in EXPECTED_FLOW_MESHES.items():
        component = components[name]
        mesh = component.get_editor_property("static_mesh")
        actual_mesh = asset_path(mesh)
        if actual_mesh != expected_mesh:
            raise RuntimeError(f"MaterialFlow mesh mismatch: {name}={actual_mesh}")
        if not component.is_visible() or component.hidden_in_game:
            raise RuntimeError(f"MaterialFlow visibility mismatch: {name}")
        bounds = mesh.get_bounds().box_extent * 2.0
        dimensions = vector_tuple(bounds)
        if not close_tuple(dimensions, EXPECTED_FLOW_BOUNDS[name]):
            raise RuntimeError(f"MaterialFlow bounds mismatch: {name}={dimensions}")
        materials = []
        for index, slot in enumerate(mesh.static_materials):
            semantic = str(slot.material_slot_name)
            expected_material = expected_flow_material(semantic)
            actual_material = asset_path(component.get_material(index))
            if actual_material != expected_material:
                raise RuntimeError(
                    f"MaterialFlow material mismatch: {name}[{index}]={actual_material}")
            materials.append(actual_material)
        transform = component.get_world_transform()
        location = vector_tuple(transform.translation)
        expected_root = s01_root if name.startswith("S01") else s07_root
        expected_location = parked.get(name, expected_root)
        if not close_tuple(location, expected_location, 0.1):
            raise RuntimeError(
                f"MaterialFlow station/mover transform mismatch: {name}={location}, expected {expected_location}")
        if not close_tuple(vector_tuple(transform.scale3d), (1.0, 1.0, 1.0), 0.001):
            raise RuntimeError(f"MaterialFlow scale drift: {name}")
        rows[name] = {
            "mesh": actual_mesh,
            "materials": materials,
            "bounds_cm": dimensions,
            "world_location_cm": location,
            "world_scale": vector_tuple(transform.scale3d),
        }
    return rows


def audit_visible_disallowed_press_content(world):
    roots = (
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
        for kind in (unreal.StaticMeshComponent, unreal.InstancedStaticMeshComponent,
                     unreal.HierarchicalInstancedStaticMeshComponent):
            for component in actor.get_components_by_class(kind):
                mesh = component.get_editor_property("static_mesh")
                path = asset_path(mesh).lower()
                if (path and any(path.startswith(root) for root in roots)
                        and component.is_visible() and not component.hidden_in_game):
                    hits.append(f"{actor.get_name()}/{component.get_name()}={path}")
    return sorted(set(hits))


def finish(result):
    global tick_handle
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def begin_screenshot(pawn, position, pitch, distance, destination, next_phase):
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


def screenshot_finished(destination):
    return task is not None and task.is_task_done() and destination.is_file() \
        and destination.stat().st_size >= 4096


def tick(_delta):
    global phase, phase_started
    try:
        now = time.monotonic()
        if now - started > 150:
            raise RuntimeError("Timed out while capturing MaterialFlow PIE evidence")
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
            begin_screenshot(pawn, unreal.Vector(-14500.0, 7000.0, 0.0),
                             -50.0, 30000.0, OVERVIEW, "wait_overview")
            return
        if phase == "wait_overview":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not screenshot_finished(OVERVIEW):
                raise RuntimeError("Overview screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            begin_screenshot(pawn, unreal.Vector(-10500.0, 7200.0, 0.0),
                             -44.0, 21000.0, OPERATOR, "wait_operator")
            return
        if phase == "wait_operator":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not screenshot_finished(OPERATOR):
                raise RuntimeError("Operator screenshot was not written")
            pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
            begin_screenshot(pawn, unreal.Vector(10500.0, 7200.0, 0.0),
                             -44.0, 21000.0, SERVICE, "wait_service")
            return
        if phase == "wait_service":
            if now - phase_started < 1.5 or not task.is_task_done():
                return
            if not screenshot_finished(SERVICE):
                raise RuntimeError("Service screenshot was not written")
            press = require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                                "native press presentation")
            components = live_static_components(press)
            disallowed = audit_visible_disallowed_press_content(world)
            if disallowed:
                raise RuntimeError("Visible disallowed press content: " + " | ".join(disallowed))
            finish({
                "$schema": "lineboss/evidence/onefactory/native-press-train-materialflow-v005/v1",
                "status": "PASS__NATIVE_PRESS_TRAIN_AND_MATERIALFLOW_V002_PIE",
                "screenshots": [str(OVERVIEW), str(OPERATOR), str(SERVICE)],
                "animated_mechanisms": press.get_animated_mechanism_count(),
                "s02_v003": audit_s02(components),
                "stagepack_v003": audit_stagepack(press, components),
                "materialflow_v002": audit_materialflow(components),
                "disallowed_visible_press_content": [],
                "content_writes": [],
                "map_loaded_or_saved": [],
            })
    except Exception as exc:
        unreal.log_error("NATIVE_PRESS_MATERIALFLOW_V005_CAPTURE_FAIL " + str(exc))
        finish({
            "$schema": "lineboss/evidence/onefactory/native-press-train-materialflow-v005/v1",
            "status": "FAIL__NATIVE_PRESS_TRAIN_AND_MATERIALFLOW_V002_PIE",
            "error": str(exc),
            "content_writes": [],
            "map_loaded_or_saved": [],
        })


try:
    if not LEVELS.load_level(MAP):
        raise RuntimeError("Could not load the OneFactory map")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as exc:
    unreal.log_error("NATIVE_PRESS_MATERIALFLOW_V005_CAPTURE_START_FAIL " + str(exc))
    finish({
        "$schema": "lineboss/evidence/onefactory/native-press-train-materialflow-v005/v1",
        "status": "FAIL__NATIVE_PRESS_TRAIN_AND_MATERIALFLOW_V002_PIE",
        "error": str(exc),
        "content_writes": [],
        "map_loaded_or_saved": [],
    })
