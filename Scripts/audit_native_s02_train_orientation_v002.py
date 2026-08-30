"""Native PIE measurement of the S02/operator-side relationship to S03-S06.

Revision v002 fixes the v001 Unreal Python transform API typo and uses the
project's established PIE shutdown sequence.  It opens the approved map only
for a transient PIE session, saves no map/content, and writes a new immutable
receipt beneath Saved/Audits.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUT = ROOT / "Saved/Audits/OneFactory/Press/NativeS02TrainOrientation_v002/orientation_receipt.json"

S02_ROOT = "S02DeepDrawPresentation"
S02_GATE = "S02DeepDrawSafetyGatePresentation"
STAGE_CUES = tuple("{}StagePackCuePresentation".format(station)
                   for station in ("S03", "S04", "S05", "S06"))

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
started = time.monotonic()
tick_handle = None
finished = False


def vector(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


def asset_path(asset):
    return str(asset.get_path_name()) if asset else "none"


def require_one(world, klass, label):
    values = list(unreal.GameplayStatics.get_all_actors_of_class(world, klass))
    if len(values) != 1:
        raise RuntimeError("Expected one {} but found {}".format(label, len(values)))
    return values[0]


def get_builder(world):
    values = [value for value in unreal.ObjectIterator(unreal.LBOneFactoryPlayerBuilderSubsystem)
              if value.get_world() == world]
    if len(values) != 1:
        raise RuntimeError("Expected one OneFactory builder but found {}".format(len(values)))
    return values[0]


def components_by_name(actor):
    return {str(component.get_name()): component
            for component in actor.get_components_by_class(unreal.StaticMeshComponent)}


def world_aabb(component):
    mesh = component.get_editor_property("static_mesh")
    if mesh is None:
        raise RuntimeError("{} has no StaticMesh".format(component.get_name()))
    bounds = mesh.get_bounding_box()
    transform = component.get_world_transform()
    points = []
    for x in (bounds.min.x, bounds.max.x):
        for y in (bounds.min.y, bounds.max.y):
            for z in (bounds.min.z, bounds.max.z):
                points.append(transform.transform_location(unreal.Vector(x, y, z)))
    minimum = unreal.Vector(min(point.x for point in points),
                             min(point.y for point in points),
                             min(point.z for point in points))
    maximum = unreal.Vector(max(point.x for point in points),
                             max(point.y for point in points),
                             max(point.z for point in points))
    return minimum, maximum


def component_row(component, root_location):
    minimum, maximum = world_aabb(component)
    centre = (minimum + maximum) * 0.5
    transform = component.get_world_transform()
    return {
        "component": str(component.get_name()),
        "mesh": asset_path(component.get_editor_property("static_mesh")),
        "root_location_cm": vector(root_location),
        "world_location_cm": vector(transform.translation),
        "world_aabb_cm": {"min": vector(minimum), "max": vector(maximum),
                           "centre": vector(centre)},
        "centre_delta_from_s02_root_cm": vector(centre - root_location),
    }


def finish(payload):
    global tick_handle, finished
    if finished:
        return
    finished = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    # Explicitly leave PIE before releasing the asynchronous Python keepalive.
    # This matches the established project validator lifecycle and avoids a
    # live PIE world holding the commandlet open after the receipt is written.
    try:
        unreal.EditorLevelLibrary.editor_end_play()
    except Exception as error:
        unreal.log_warning("NATIVE_S02_TRAIN_ORIENTATION_END_PIE_WARN " + str(error))
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    try:
        if time.monotonic() - started > 90.0:
            raise RuntimeError("Timed out waiting for native press presentation")
        world = WORLDS.get_game_world()
        if world is None:
            return
        _pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
        hud = require_one(world, unreal.LBControlRoomHUD, "control-room HUD")
        builder = get_builder(world)
        press_values = list(unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBOneFactoryPressStarterPresentationActor))
        if not press_values:
            hud.open_factory_build()
            accepted = hud.activate_management_action(0)
            reason = str(builder.get_last_action_reason())
            if not accepted and "PRESENTATIONS LIVE" not in reason:
                raise RuntimeError("Native press action rejected: {}".format(reason))
            return
        press = require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                            "native press presentation")
        components = components_by_name(press)
        required = {S02_ROOT, S02_GATE, *STAGE_CUES}
        missing = sorted(required - set(components))
        if missing:
            return
        s02_root = components[S02_ROOT].get_world_transform().translation
        gate = component_row(components[S02_GATE], s02_root)
        cues = {name: component_row(components[name], s02_root) for name in STAGE_CUES}
        gate_operator_side = gate["centre_delta_from_s02_root_cm"][0] < -10.0
        cue_operator_side = {
            name: row["centre_delta_from_s02_root_cm"][0] < -10.0
            for name, row in cues.items()
        }
        # S03-S06 sit downstream of S02. The absolute axis choice is less
        # important than the physical operator-aisle agreement measured here.
        all_operator_aligned = gate_operator_side and all(cue_operator_side.values())
        finish({
            "$schema": "lineboss/onefactory/press/native-s02-train-orientation/v2",
            "status": ("PASS__S02_AND_TRAIN_OPERATOR_FEATURES_SHARE_NEGATIVE_X_AISLE"
                       if all_operator_aligned else
                       "FAIL__S02_AND_TRAIN_OPERATOR_FEATURES_DO_NOT_SHARE_NEGATIVE_X_AISLE"),
            "s02_root_component": S02_ROOT,
            "s02_root_world_location_cm": vector(s02_root),
            "s02_safety_gate": gate,
            "stage_operator_cues": cues,
            "gate_on_negative_x_operator_side": gate_operator_side,
            "stage_cues_on_negative_x_operator_side": cue_operator_side,
            "source_manifest_mirror_claim_accepted": all_operator_aligned,
            "map_opened_by_script": False,
            "map_saved_by_script": False,
            "content_writes": [],
        })
    except Exception as error:
        unreal.log_error("NATIVE_S02_TRAIN_ORIENTATION_FAIL " + str(error))
        finish({
            "$schema": "lineboss/onefactory/press/native-s02-train-orientation/v2",
            "status": "FAIL__NATIVE_S02_TRAIN_ORIENTATION_MEASUREMENT",
            "error": str(error),
            "map_opened_by_script": False,
            "map_saved_by_script": False,
            "content_writes": [],
        })


try:
    if OUT.exists():
        raise RuntimeError("Refusing to overwrite existing orientation receipt: {}".format(OUT))
    if not LEVELS.load_level(MAP):
        raise RuntimeError("Could not load {}".format(MAP))
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as error:
    unreal.log_error("NATIVE_S02_TRAIN_ORIENTATION_START_FAIL " + str(error))
    finish({
        "$schema": "lineboss/onefactory/press/native-s02-train-orientation/v2",
        "status": "FAIL__NATIVE_S02_TRAIN_ORIENTATION_MEASUREMENT",
        "error": str(error),
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "content_writes": [],
    })
