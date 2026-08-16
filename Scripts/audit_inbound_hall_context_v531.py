"""Read-only actor-label audit for the isolated v531 validation hall."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level("/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v531"):
    raise RuntimeError("Could not load v531 for hall audit")

tokens = ("wall", "roof", "floor", "light", "backdrop", "column", "beam")
rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if any(token in label.lower() for token in tokens):
        loc = actor.get_actor_location()
        scale = actor.get_actor_scale3d()
        rows.append({
            "label": label,
            "class": actor.get_class().get_name(),
            "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
            "scale": [round(scale.x, 3), round(scale.y, 3), round(scale.z, 3)],
        })

out = project / "Saved/Audits/PressShopIntegration/inbound_hall_actor_audit_v531.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"status": "READ_ONLY", "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_INBOUND_HALL_AUDIT_V531 {len(rows)}")
