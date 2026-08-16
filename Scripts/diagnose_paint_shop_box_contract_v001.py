"""Read-only transient diagnosis for Paint Shop box-component contracts.

Loads the rejected blank Paint prototype package, creates three temporary cube
actors, records their live transform/component state, destroys them, and never
saves the level or any asset.
"""

from __future__ import annotations

import json

import unreal


MAP = "/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001"


def describe(actor) -> dict:
    component = actor.get_editor_property("static_mesh_component")
    location = actor.get_actor_location()
    scale = actor.get_actor_scale3d()
    mesh = component.get_editor_property("static_mesh")
    material = component.get_material(0)
    collision = component.get_collision_enabled()
    return {
        "label": actor.get_actor_label(),
        "location": [float(location.x), float(location.y), float(location.z)],
        "scale": [float(scale.x), float(scale.y), float(scale.z)],
        "mesh": mesh.get_path_name() if mesh else None,
        "material": material.get_path_name() if material else None,
        "collision_text": str(collision),
        "collision_value": int(collision.value),
        "collision_profile": str(component.get_collision_profile_name()),
        "navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        "cast_shadow": bool(component.get_editor_property("cast_shadow")),
    }


def main() -> None:
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if levels is None or actors is None or not levels.load_level(MAP):
        raise RuntimeError("Could not load rejected Paint map for transient diagnosis")

    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    yellow = unreal.load_asset("/Game/LineBoss/Materials/M_LB_SafetyYellow")
    if cube is None or yellow is None:
        raise RuntimeError("Required diagnostic cube/material unavailable")

    rows = []
    spawned = []
    try:
        for index, (label, dimensions, collision_mode) in enumerate((
            ("LB_PS_DIAG_SetEnabledNoCollision", (1900.0, 10.0, 1.0), "set_enabled"),
            ("LB_PS_DIAG_ProfileNoCollision", (5400.0, 300.0, 0.8), "profile"),
            ("LB_PS_DIAG_QueryAndPhysics", (1900.0, 10.0, 1.0), "collision"),
        )):
            actor = actors.spawn_actor_from_class(
                unreal.StaticMeshActor,
                unreal.Vector(0.0, float(index * 400), 100.0),
                unreal.Rotator(),
            )
            if actor is None:
                raise RuntimeError(f"Could not spawn {label}")
            spawned.append(actor)
            actor.set_actor_label(label)
            actor.set_actor_scale3d(unreal.Vector(
                dimensions[0] / 100.0,
                dimensions[1] / 100.0,
                dimensions[2] / 100.0,
            ))
            component = actor.get_editor_property("static_mesh_component")
            component.set_static_mesh(cube)
            component.set_material(0, yellow)
            if collision_mode == "profile":
                component.set_collision_profile_name("NoCollision")
            else:
                component.set_collision_enabled(
                    unreal.CollisionEnabled.QUERY_AND_PHYSICS
                    if collision_mode == "collision" else unreal.CollisionEnabled.NO_COLLISION
                )
            component.set_editor_property("can_ever_affect_navigation", False)
            component.set_cast_shadow(False)
            rows.append(describe(actor))
    finally:
        for actor in spawned:
            actors.destroy_actor(actor)

    unreal.log("LINE_BOSS_PAINT_BOX_DIAGNOSTIC=" + json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
