"""Read-only inventory of installed service-dock actors in retained v269."""
import json
from pathlib import Path
from datetime import datetime, timezone

import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/press_shop_installed_service_docks_v269.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")

records = []
for actor in actors.get_all_level_actors():
    meshes = actor.get_components_by_class(unreal.StaticMeshComponent)
    paths = []
    for component in meshes:
        mesh = component.static_mesh
        if mesh:
            path = mesh.get_path_name()
            if "ServiceDock" in path or "DockCore" in path:
                paths.append(path)
    if paths or "Dock" in actor.get_actor_label():
        transform = actor.get_actor_transform()
        records.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_path_name(),
            "location_cm": [round(transform.translation.x, 3), round(transform.translation.y, 3), round(transform.translation.z, 3)],
            "rotation_deg": [round(transform.rotation.rotator().pitch, 3), round(transform.rotation.rotator().yaw, 3), round(transform.rotation.rotator().roll, 3)],
            "scale": [round(transform.scale3d.x, 4), round(transform.scale3d.y, 4), round(transform.scale3d.z, 4)],
            "mesh_paths": sorted(paths),
            "tags": sorted(str(tag) for tag in actor.tags),
        })

payload = {
    "$schema": "cairnwell/audit/press-shop-installed-service-docks-v269/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY",
    "map": MAP,
    "records": sorted(records, key=lambda item: item["label"]),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_V269_AUDIT {len(records)}")
