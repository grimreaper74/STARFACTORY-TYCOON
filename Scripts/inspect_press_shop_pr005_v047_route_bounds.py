"""Read-only bounds audit for v047 route surfaces."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_v047_route_bounds.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
rows = []
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_PR005_V047_"):
        continue
    origin, extent = actor.get_actor_bounds(False)
    scale = actor.get_actor_scale3d()
    location = actor.get_actor_location()
    rows.append({
        "actor": actor.get_actor_label(),
        "location_cm": [location.x, location.y, location.z],
        "scale": [scale.x, scale.y, scale.z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "material_0": (actor.static_mesh_component.get_material(0).get_path_name()
                       if isinstance(actor, unreal.StaticMeshActor)
                       and actor.static_mesh_component.get_material(0) is not None else None),
        "hidden": bool(actor.get_editor_property("hidden")),
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_V047_ROUTE_BOUNDS_PASS actors={len(rows)}")
unreal.SystemLibrary.quit_editor()
