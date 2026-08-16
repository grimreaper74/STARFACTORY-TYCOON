"""Record v514 actor labels, transforms and mesh material slots for visual correction."""
from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v514"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_installed_cell_actor_audit_v514.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v514")
records=[]
for actor in actors.get_all_level_actors():
    row={"label":actor.get_actor_label(), "class":actor.get_class().get_name(),
         "location":[round(v,2) for v in (actor.get_actor_location().x,actor.get_actor_location().y,actor.get_actor_location().z)]}
    if isinstance(actor, unreal.StaticMeshActor):
        mesh=actor.static_mesh_component.get_editor_property("static_mesh")
        row["mesh"]=mesh.get_path_name() if mesh else None
        row["slots"]=[str(v.get_editor_property("material_slot_name")) for v in mesh.get_editor_property("static_materials")] if mesh else []
    records.append(row)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map":MAP,"actors":records},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_V514_ACTOR_AUDIT_PASS")
