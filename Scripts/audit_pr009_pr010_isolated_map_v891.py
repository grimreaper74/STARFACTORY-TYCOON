from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_OriginalFBX_Isolated_v884';levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
rows=[]
for a in actors.get_all_level_actors():
 r={'label':a.get_actor_label(),'class':a.get_class().get_name(),'location':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],'hidden':a.is_hidden_ed()}
 if isinstance(a,unreal.StaticMeshActor):
  m=a.static_mesh_component.get_editor_property('static_mesh');r['mesh']=m.get_path_name() if m else None
  if m:
   d=m.get_bounds().box_extent*2;r['mesh_bounds_cm']=[d.x,d.y,d.z];r['visible']=a.static_mesh_component.get_editor_property('visible')
 rows.append(r)
out=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_isolated_map_actor_audit_v891.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'map':MAP,'actor_count':len(rows),'actors':rows},indent=2),encoding='utf-8');print(json.dumps({'actor_count':len(rows),'matching':[r for r in rows if 'PR009' in r['label'] or 'PR010' in r['label']]},indent=2))
