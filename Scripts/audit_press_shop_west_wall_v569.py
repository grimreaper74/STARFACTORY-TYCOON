"""Read-only audit of actors at the west end of the direct-v438 child."""
from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v568"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_west_wall_v569.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v568")
rows=[]
for actor in actors.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False)
    if origin.x + extent.x < -9000 or origin.x - extent.x < -9000:
        mesh = None
        if isinstance(actor, unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh:
            mesh = actor.static_mesh_component.static_mesh.get_path_name()
        rows.append({"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"asset":mesh,
                     "origin":[origin.x,origin.y,origin.z],"extent":[extent.x,extent.y,extent.z],
                     "tags":[str(t) for t in actor.tags]})
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"map":MAP,"actors":rows},indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_WEST_WALL_AUDIT_V569_PASS actors={len(rows)}")
