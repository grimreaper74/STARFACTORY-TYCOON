"""Transplant Codex's reference press shop into the playable Moorcross map.

Replaces the lossy manifest pipeline. The manifest captured 2,804 of 4,092 actors,
carried NO lights at all, and 418 of its entries were engine primitives - which is
why the Moorcross press shop was missing its roof, lighting, signage and conveyors.

This reads the reference level LIVE and records each actor's mesh, its PER-SLOT
material bindings and its light properties, then reopens the playable map and
rebuilds them. Reading live rather than from a JSON dump is deliberate: the dump
aggregates materials into a set, which loses slot order and therefore any override.

Two exclusions, both measured (see the verified correction in
Docs/OneFactory/PLANT_LAYOUT_PLAN_2026-08-17.md):
  * CameraActors - viewpoints, not geometry. 106 of them, one sitting 8,500 cm
    south of the south wall, and they inflated the apparent footprint to 205 m.
  * Ten stretched robot-arm actors on the PTC/PTD S07 stations, posed far outside
    the shell. A genuine authoring defect in the reference.
With those set aside the content measures 236 x 120 m against a 320 x 130 m bay, so
it fits with no bay resize, no re-layout and NO ROTATION - the +90 degree
datum-local yaw in LBOneFactoryDevRestoredShopActor was the bug.

The reference map is PROTECTED and is only ever read here.

Run headless. It MUST be -ExecutePythonScript: under -run=pythonscript there is no
editor world, so load_level and every spawn silently return nothing and the script
still exits 0.
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/transplant_press_shop.py
"""
import io
import json
import os

import unreal

REFERENCE = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Press.Transplant"
OUT = os.environ.get("LB_TRANSPLANT_OUT", "C:/Temp/lb_transplant.json")

# The press bay from LBOneFactoryTypes.cpp MakeMoorcrossWorksShellLayout.
PRESS_BAY_CENTRE = unreal.Vector(-14500.0, 8000.0, 0.0)
PRESS_BAY_SIZE = unreal.Vector(32000.0, 13000.0, 2000.0)

STRAY_TOKENS = ("PTC_S07_Runtime", "PTD_S07_Runtime")
STRAY_MIN_Y = 5400.0

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

REPORT = {"source": REFERENCE, "target": TARGET, "notes": []}


def require_world(path):
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None or path.rsplit("/", 1)[-1] != world.get_name():
        raise RuntimeError(
            "expected world '{}' but the editor has '{}'. Use "
            "-ExecutePythonScript, not -run=pythonscript.".format(
                path.rsplit("/", 1)[-1],
                "<none>" if world is None else world.get_name()))


# ---------------------------------------------------------------------------
# Phase 1: read the reference. Asset references survive the level change, so
# meshes and materials captured here stay valid when the target map is opened.
# ---------------------------------------------------------------------------
if not LEVEL_SUB.load_level(REFERENCE):
    raise RuntimeError("could not load {}".format(REFERENCE))
require_world(REFERENCE)

records = []
skipped_cameras = 0
skipped_strays = []
skipped_empty = 0

for actor in ACTOR_SUB.get_all_level_actors():
    if actor is None:
        continue
    label = actor.get_actor_label() or actor.get_name()

    if isinstance(actor, unreal.CameraActor):
        skipped_cameras += 1
        continue
    location = actor.get_actor_location()
    if location.y > STRAY_MIN_Y and any(t in label for t in STRAY_TOKENS):
        skipped_strays.append({"label": label, "y": round(location.y, 1)})
        continue

    entry = {
        "label": label,
        "loc": (location.x, location.y, location.z),
        "rot": actor.get_actor_rotation(),
        "scale": actor.get_actor_scale3d(),
        "tags": [str(t) for t in actor.tags],
        "meshes": [],
        "light": None,
    }

    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        asset = component.static_mesh
        if asset is None:
            continue
        # Skip anything carrying Meshy / ExternalGenerated provenance. The bootstrap
        # guard rejects it, and that guard is right: the project's policy is
        # Blender-native art only. Exempting it by tag would defeat the guard rather
        # than satisfy it, so the content is left out and recorded as a gap instead.
        # In practice this costs exactly two dressing meshes across the four press
        # trains - an electrical net and an operator HMI panel - not the presses.
        poisoned = None
        candidates = [asset.get_path_name()]
        for slot_index in range(component.get_num_materials()):
            bound_material = component.get_material(slot_index)
            if bound_material is not None:
                candidates.append(bound_material.get_path_name())
        for candidate in candidates:
            lowered = candidate.lower()
            if "meshy" in lowered or "externalgenerated" in lowered:
                poisoned = candidate
                break
        if poisoned is not None:
            REPORT.setdefault("skipped_provenance", []).append(
                poisoned.rsplit("/", 1)[-1])
            continue
        # Per-slot materials, in slot order, so overrides survive.
        slots = []
        for index in range(component.get_num_materials()):
            bound = component.get_material(index)
            # Some reference actors carry runtime MaterialInstanceDynamics. A MID is
            # not an asset and cannot be assigned to a saved actor, so resolve it to
            # its parent, which is a real MaterialInterface. Without this the whole
            # transplant dies on "Cannot nativize 'MaterialInstanceDynamic'".
            if isinstance(bound, unreal.MaterialInstanceDynamic):
                try:
                    parent = bound.get_editor_property("parent")
                except Exception:  # noqa: BLE001
                    parent = None
                REPORT.setdefault("dynamic_materials_resolved", 0)
                REPORT["dynamic_materials_resolved"] += 1
                bound = parent
            slots.append(bound)
        # Record each component's WORLD transform, not the actor's. Placing every
        # mesh at its actor origin collapses multi-component actors onto their pivot
        # and drops any component offset - which put large structural panels on top
        # of the camera and made every capture identical regardless of pitch.
        # 3,793 actors carry 5,129 mesh components, so this affects over a thousand
        # of them. Taking the world transform avoids composing rotations by hand.
        entry["meshes"].append({
            "asset": asset,
            "slots": slots,
            "world": component.get_world_transform(),
        })

    if isinstance(actor, unreal.Light):
        component = actor.light_component
        props = {"class": actor.get_class()}
        if component:
            for name in ("intensity", "light_color", "attenuation_radius",
                         "cast_shadows", "temperature", "use_temperature",
                         "source_radius", "source_length", "outer_cone_angle",
                         "inner_cone_angle", "intensity_units",
                         "source_width", "source_height"):
                try:
                    props[name] = component.get_editor_property(name)
                except Exception:  # noqa: BLE001 - property set varies by class
                    pass
        entry["light"] = props

    if not entry["meshes"] and entry["light"] is None:
        skipped_empty += 1
        continue
    records.append(entry)

REPORT["read"] = {
    "kept": len(records),
    "skipped_cameras": skipped_cameras,
    "skipped_strays": skipped_strays,
    "skipped_no_visual": skipped_empty,
}

xs = [r["loc"][0] for r in records]
ys = [r["loc"][1] for r in records]
zs = [r["loc"][2] for r in records]
content_centre = unreal.Vector((min(xs) + max(xs)) * 0.5,
                               (min(ys) + max(ys)) * 0.5, 0.0)
size_x = max(xs) - min(xs)
size_y = max(ys) - min(ys)
REPORT["content"] = {
    "footprint_m": [round(size_x / 100.0, 1), round(size_y / 100.0, 1)],
    "centre": [round(content_centre.x, 1), round(content_centre.y, 1)],
    "z_range": [round(min(zs), 1), round(max(zs), 1)],
    "fits_bay": bool(size_x <= PRESS_BAY_SIZE.x and size_y <= PRESS_BAY_SIZE.y),
}
if not REPORT["content"]["fits_bay"]:
    raise RuntimeError(
        "content {:.0f}x{:.0f} does not fit the {:.0f}x{:.0f} press bay - "
        "re-check the exclusions before placing anything".format(
            size_x, size_y, PRESS_BAY_SIZE.x, PRESS_BAY_SIZE.y))

# Straight translation, no rotation: the content is long in X and so is the bay.
OFFSET = unreal.Vector(PRESS_BAY_CENTRE.x - content_centre.x,
                       PRESS_BAY_CENTRE.y - content_centre.y, 0.0)
REPORT["offset"] = [round(OFFSET.x, 1), round(OFFSET.y, 1)]
REPORT["notes"].append(
    "no rotation applied; the +90 degree datum-local yaw in "
    "LBOneFactoryDevRestoredShopActor pushed content outside the building")

# ---------------------------------------------------------------------------
# Phase 2: rebuild into the playable map.
# ---------------------------------------------------------------------------
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load {}".format(TARGET))
require_world(TARGET)

cleared = 0
for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        cleared += 1

placed_meshes = 0
placed_lights = 0
failures = []

for entry in records:
    target_location = unreal.Vector(entry["loc"][0] + OFFSET.x,
                                    entry["loc"][1] + OFFSET.y,
                                    entry["loc"][2])
    tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
            unreal.Name("LB.NotProcessWIP")]

    for mesh_entry in entry["meshes"]:
        world = mesh_entry["world"]
        source = world.translation
        component_location = unreal.Vector(source.x + OFFSET.x,
                                           source.y + OFFSET.y, source.z)
        actor = ACTOR_SUB.spawn_actor_from_object(
            mesh_entry["asset"], component_location, world.rotation.rotator())
        if actor is None:
            failures.append("mesh spawn failed: {}".format(entry["label"]))
            continue
        actor.set_actor_scale3d(world.scale3d)
        component = actor.static_mesh_component
        if component:
            for index, material in enumerate(mesh_entry["slots"]):
                if material is not None:
                    component.set_material(index, material)
        actor.tags = tags
        actor.set_actor_label("PT_" + entry["label"])
        placed_meshes += 1

    if entry["light"] is not None:
        props = entry["light"]
        actor = ACTOR_SUB.spawn_actor_from_class(
            props["class"], target_location, entry["rot"])
        if actor is None:
            failures.append("light spawn failed: {}".format(entry["label"]))
            continue
        component = getattr(actor, "light_component", None)
        if component:
            for name, value in props.items():
                if name == "class":
                    continue
                try:
                    component.set_editor_property(name, value)
                except Exception:  # noqa: BLE001 - not every class has every one
                    pass
        actor.tags = tags
        actor.set_actor_label("PT_" + entry["label"])
        placed_lights += 1

REPORT["placed"] = {"meshes": placed_meshes, "lights": placed_lights,
                    "cleared_previous": cleared, "failures": len(failures)}
REPORT["failures_sample"] = failures[:10]

LEVEL_SUB.save_current_level()

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True, default=str))
unreal.log(
    "LINE_BOSS_PRESS_TRANSPLANT placed {} mesh + {} light actors (cleared {}, "
    "{} failures) footprint {} m offset {} -> {}".format(
        placed_meshes, placed_lights, cleared, len(failures),
        REPORT["content"]["footprint_m"], REPORT["offset"], OUT))
