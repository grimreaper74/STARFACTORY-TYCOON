"""Read-only local actor inventory before shifting PR-004 off the dark floor strip."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_local_cluster_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    location = actor.get_actor_location()
    if not (-5900.0 <= location.x <= -4400.0 and -2600.0 <= location.y <= -1250.0):
        continue
    meshes = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None:
            meshes.append(mesh.get_path_name())
    rows.append({"actor": actor.get_actor_label(), "class": actor.get_class().get_name(),
                 "location_cm": [location.x, location.y, location.z],
                 "tags": [str(tag) for tag in actor.tags], "meshes": meshes})

rows.sort(key=lambda row: row["actor"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "bounds_cm": {"x": [-5900, -4400], "y": [-2600, -1250]},
                           "actor_count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_LOCAL_CLUSTER_AUDIT_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
