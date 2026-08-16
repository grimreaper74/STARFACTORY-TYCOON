"""Read-only inventory of retained dock actors used for Press Shop integration."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
EXPECTED_MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v013"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_actor_assets_v024.json"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world else ""
if current != EXPECTED_MAP:
    raise RuntimeError(f"One-map rule violation: opened {current}, expected {EXPECTED_MAP}")

rows = []
for actor in ACTORS.get_all_level_actors():
    label = actor.get_actor_label()
    if label not in ("LB_DOCK_INTAKE_MR01_v005", "LB_DOCK_INTAKE_CR01_v008"):
        continue
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError(f"{label} is not a StaticMeshActor")
    component = actor.static_mesh_component
    mesh = component.static_mesh
    materials = []
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        materials.append(material.get_path_name() if material else None)
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    rows.append({
        "label": label,
        "mesh": mesh.get_path_name() if mesh else None,
        "location_cm": [location.x, location.y, location.z],
        "rotation_roll_pitch_yaw_deg": [rotation.roll, rotation.pitch, rotation.yaw],
        "scale": [scale.x, scale.y, scale.z],
        "materials": materials,
        "collision_enabled": str(component.get_collision_enabled()),
        "collision_profile": str(component.get_collision_profile_name()),
    })

if len(rows) != 2:
    raise RuntimeError(f"Expected two retained dock actors, found {len(rows)}")

payload = {
    "$schema": "cairnwell/audit/service-dock-actor-assets-v024/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_RETAINED_DOCK_ACTOR_ASSET_INVENTORY",
    "map": current,
    "actors": rows,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_ACTOR_ASSETS_V024_PASS")
unreal.SystemLibrary.quit_editor()
