"""Read-only inventory of the retained isolated inbound v551 map."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not level.load_level("/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v551"):
    raise RuntimeError("Could not load inbound v551")

rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("LB_INBOUND_"):
        continue
    mesh_path = None
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        mesh = component.get_editor_property("static_mesh")
        mesh_path = mesh.get_path_name() if mesh else None
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "mesh": mesh_path,
        "location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
        "rotation_deg": [round(rotation.roll, 2), round(rotation.pitch, 2), round(rotation.yaw, 2)],
        "collision_enabled": str(component.get_collision_enabled()) if component else None,
        "can_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")) if component else None,
    })

out = project / "Saved/Audits/PressShopIntegration/inbound_installed_actor_inventory_v551.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"map": "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v551", "actor_count": len(rows), "actors": sorted(rows, key=lambda x: x["label"])}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_INBOUND_V551_ACTOR_AUDIT_PASS count={len(rows)}")
