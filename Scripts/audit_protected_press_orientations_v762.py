from pathlib import Path
import json,unreal
MAP='/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438';OUT=Path(unreal.Paths.project_dir())/'Saved/Audits/PressShopIntegration/protected_press_orientation_readonly_v762.json'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError('Could not read protected v438')
rows=[]
for a in actors.get_all_level_actors():
 label=a.get_actor_label();tags=[str(t) for t in a.tags];mesh=''
 if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:mesh=a.static_mesh_component.static_mesh.get_path_name()
 hay=(label+' '+mesh+' '+' '.join(tags)).lower()
 if any(k in hay for k in ['pressbody','press_body','press shell','press_shell','pressframe','press_frame','press train','presstrain']):
  r=a.get_actor_rotation();l=a.get_actor_location();rows.append({'label':label,'location_cm':[l.x,l.y,l.z],'rotation_deg':[r.roll,r.pitch,r.yaw],'mesh':mesh,'tags':tags})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'map':MAP,'read_only':True,'matches':len(rows),'actors':rows},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PROTECTED_PRESS_ORIENTATION_V762_WRITTEN')
