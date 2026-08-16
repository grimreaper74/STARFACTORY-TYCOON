"""Read-only inventory of collision-bearing actors across the west-bay nav seam."""
from pathlib import Path
import json, unreal
MAP="/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavCandidate_v581"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/PressShopIntegration/inbound_nav_barrier_v584.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
rows=[]
for actor in actors.get_all_level_actors():
    origin,extent=actor.get_actor_bounds(False,False)
    if origin.x-extent.x <= -9348 <= origin.x+extent.x and origin.y+extent.y >= -4800 and origin.y-extent.y <= -2500:
        collision=[]
        for comp in actor.get_components_by_class(unreal.PrimitiveComponent):
            try: collision.append(str(comp.get_collision_enabled()))
            except Exception: pass
        rows.append({"label":actor.get_actor_label(),"class":actor.get_class().get_name(),
          "origin_cm":[origin.x,origin.y,origin.z],"extent_cm":[extent.x,extent.y,extent.z],
          "collision":sorted(set(collision)),"tags":sorted(str(t) for t in actor.tags)})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"map":MAP,"actors":rows},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_NAV_BARRIER_V584_COMPLETE")
