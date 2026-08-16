"""Read-only audit of signage and controls in retained inbound visual map v548."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
level = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v548"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(level):
    raise RuntimeError("Failed loading v548")

rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if isinstance(actor, unreal.TextRenderActor) or any(token in label.lower() for token in ("sign", "control", "hmi", "traffic", "scanner")):
        location = actor.get_actor_location()
        rotation = actor.get_actor_rotation()
        row = {
            "label": label,
            "class": actor.get_class().get_name(),
            "location": [location.x, location.y, location.z],
            "rotation": [rotation.roll, rotation.pitch, rotation.yaw],
        }
        if isinstance(actor, unreal.TextRenderActor):
            row["text"] = str(actor.text_render.get_editor_property("text"))
            row["world_size"] = float(actor.text_render.get_editor_property("world_size"))
        rows.append(row)

out = project / "Saved/Audits/PressShopIntegration/inbound_v548_signage_audit_v549.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"status": "READ_ONLY", "map": level, "actors": rows}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_SIGNAGE_AUDIT_V549_PASS")
