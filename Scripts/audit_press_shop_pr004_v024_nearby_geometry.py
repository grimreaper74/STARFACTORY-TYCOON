"""Read-only geometry inventory around the v024 PR-004 preparation stand."""

import json
import math
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
CENTRE = unreal.Vector(-5050.0, -2000.0, 0.0)
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_v024_nearby_geometry.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    location = actor.get_actor_location()
    distance = math.hypot(location.x - CENTRE.x, location.y - CENTRE.y)
    if distance > 1900.0:
        continue
    origin, extent = actor.get_actor_bounds(False)
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    meshes = []
    for component in components:
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None:
            meshes.append(mesh.get_path_name())
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_path_name(),
        "location_cm": [location.x, location.y, location.z],
        "distance_xy_cm": distance,
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "bounds_bottom_cm": origin.z - extent.z,
        "bounds_top_cm": origin.z + extent.z,
        "meshes": meshes,
    })

rows.sort(key=lambda item: item["distance_xy_cm"])
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_V024_NEARBY_GEOMETRY_AUDIT_PASS actors={len(rows)} output={OUTPUT}")
unreal.SystemLibrary.quit_editor()
