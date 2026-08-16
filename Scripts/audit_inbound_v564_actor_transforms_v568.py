"""Read-only transform/asset inventory for the retained v564 inbound composition."""
from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v564"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_v564_actor_transforms_v568.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

records = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not (label.startswith("LB_INBOUND_") or label.startswith("LB_CAM_Inbound")):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    asset = None
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        asset = mesh.get_path_name() if mesh else None
    records.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "asset": asset,
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
        "scale": [scale.x, scale.y, scale.z],
        "tags": [str(tag) for tag in actor.tags],
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "read_only": True, "actors": records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_INBOUND_V564_TRANSFORM_AUDIT_PASS actors={len(records)}")
