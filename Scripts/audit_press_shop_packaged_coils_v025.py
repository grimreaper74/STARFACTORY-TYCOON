"""Read-only inventory of packaged-coil actors/components in the v025 map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_packaged_coils_v025.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    meshes = []
    for component in components:
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None and "MasterCoil" in mesh.get_path_name():
            location = component.get_world_location()
            rotation = component.get_world_rotation()
            scale = component.get_world_scale()
            meshes.append({
                "component": component.get_name(),
                "mesh": mesh.get_path_name(),
                "world_location_cm": [location.x, location.y, location.z],
                "world_rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
                "world_scale": [scale.x, scale.y, scale.z],
                "visible": component.is_visible(),
                "materials": [
                    component.get_material(index).get_path_name() if component.get_material(index) is not None else None
                    for index in range(component.get_num_materials())
                ],
            })
    if meshes:
        rows.append({
            "actor": actor.get_actor_label(),
            "class": actor.get_class().get_path_name(),
            "tags": [str(tag) for tag in actor.tags],
            "packaged_components": meshes,
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-packaged-coils-v025/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "actor_count": len(rows),
    "actors": sorted(rows, key=lambda row: row["actor"]),
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PACKAGED_COIL_AUDIT_V025_PASS actors={len(rows)} output={OUT}")
unreal.SystemLibrary.quit_editor()
