"""Read-only inventory of bin/waste actors around the v026 PR-004 candidate."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_bins_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    mesh_paths = []
    for component in components:
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None:
            mesh_paths.append(mesh.get_path_name())
    searchable = " ".join([label, *tags, *mesh_paths]).lower()
    if "bin" not in searchable and "waste" not in searchable:
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    rows.append({
        "actor": label,
        "tags": tags,
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
        "meshes": mesh_paths,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "bin_or_waste_actor_count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_BIN_AUDIT_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
