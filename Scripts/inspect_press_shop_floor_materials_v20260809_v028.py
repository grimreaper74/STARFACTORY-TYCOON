from pathlib import Path
import json, unreal
ROOT=Path(unreal.Paths.project_dir())
MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v029'
OUT=ROOT/'Saved/Audits/PressShopIntegration/clean_full_floor_material_inspection_v20260809_v030.json'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level(MAP)
rows=[]
for a in actors.get_all_level_actors():
    if isinstance(a,unreal.StaticMeshActor) and (a.get_actor_label()=='LB_CLEAN_Floor_220m_x_120m' or 'LB.FloorPaint.FullShop' in {str(x) for x in a.tags}):
        m=a.static_mesh_component.get_material(0)
        rows.append({'label':a.get_actor_label(),'material':m.get_path_name() if m else None,'tags':[str(x) for x in a.tags]})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'map':MAP,'count':len(rows),'rows':rows},indent=2),encoding='utf-8')
