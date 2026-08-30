"""Read-only PIE inventory of environment dressing visible around the native press shop."""

import json
from pathlib import Path
import time

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUT = ROOT / "Saved/Audits/OneFactory/Press/PhotoEnvironment_v001/photo_environment_v001.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
started = time.monotonic()
tick_handle = None
finished = False
phase = "wait_world"
phase_started = started


def vector(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


def path_of(asset):
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


def environment_actor_row(actor):
    origin, extent = actor.get_actor_bounds(False)
    components = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        count = None
        try:
            count = int(component.get_instance_count())
        except Exception:
            pass
        components.append({
            "name": str(component.get_name()),
            "class": str(component.get_class().get_name()),
            "mesh": path_of(mesh),
            "visible": bool(component.is_visible()),
            "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            "instance_count": count,
            "bounds_origin_cm": vector(component.bounds.origin),
            "bounds_extent_cm": vector(component.bounds.box_extent),
        })
    return {
        "label": str(actor.get_actor_label()),
        "name": str(actor.get_name()),
        "class": str(actor.get_class().get_name()),
        "tags": sorted(str(tag) for tag in actor.tags),
        "hidden": bool(actor.hidden),
        "bounds_origin_cm": vector(origin),
        "bounds_extent_cm": vector(extent),
        "components": components,
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
    try:
        unreal.EditorLevelLibrary.editor_end_play()
    except Exception as error:
        unreal.log_warning("PRESS_PHOTO_ENVIRONMENT_AUDIT_END_PIE_WARN " + str(error))
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started
    try:
        now = time.monotonic()
        if now - started > 90.0:
            raise RuntimeError(f"Timed out in phase {phase}")
        world = WORLDS.get_game_world()
        if world is None:
            return
        if phase == "wait_world":
            if now - phase_started < 4.0:
                return
            hud = require_one(world, unreal.LBControlRoomHUD, "control-room HUD")
            builder = get_builder(world)
            if not unreal.GameplayStatics.get_all_actors_of_class(
                    world, unreal.LBOneFactoryPressStarterPresentationActor):
                hud.open_factory_build()
                accepted = hud.activate_management_action(0)
                reason = str(builder.get_last_action_reason())
                if not accepted and "PRESENTATIONS LIVE" not in reason:
                    raise RuntimeError("New Factory action rejected: " + reason)
            hud.close_management()
            phase = "audit"
            phase_started = now
            return
        if phase == "audit":
            if now - phase_started < 2.0:
                return
            require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                        "native press presentation")
            environment_rows = []
            for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
                tags = [str(tag).lower() for tag in actor.tags]
                label = str(actor.get_actor_label()).lower()
                klass = str(actor.get_class().get_name()).lower()
                if (any("environment" in tag or "envelope" in tag for tag in tags)
                        or "envelope" in label or "envelope" in klass
                        or "side" in label and "dress" in label):
                    environment_rows.append(environment_actor_row(actor))
            finish({
                "$schema": "lineboss/evidence/onefactory/press-photo-environment-v001/v1",
                "status": "PASS__PIE_ENVIRONMENT_DRESSING_INVENTORY",
                "environment_actor_count": len(environment_rows),
                "environment_actors": sorted(environment_rows, key=lambda row: row["label"]),
                "map_loaded_or_saved": [],
                "content_writes": [],
            })
    except Exception as error:
        unreal.log_error("PRESS_PHOTO_ENVIRONMENT_AUDIT_FAIL " + str(error))
        finish({
            "$schema": "lineboss/evidence/onefactory/press-photo-environment-v001/v1",
            "status": "FAIL__PIE_ENVIRONMENT_DRESSING_INVENTORY",
            "error": str(error),
            "map_loaded_or_saved": [],
            "content_writes": [],
        })


try:
    if OUT.exists():
        raise RuntimeError(f"Refusing to overwrite prior environment audit: {OUT}")
    if not LEVELS.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as error:
    unreal.log_error("PRESS_PHOTO_ENVIRONMENT_AUDIT_START_FAIL " + str(error))
    finish({
        "$schema": "lineboss/evidence/onefactory/press-photo-environment-v001/v1",
        "status": "FAIL__PIE_ENVIRONMENT_DRESSING_INVENTORY",
        "error": str(error),
        "map_loaded_or_saved": [],
        "content_writes": [],
    })
