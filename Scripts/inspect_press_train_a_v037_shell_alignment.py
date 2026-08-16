import json,unreal
MAP="/Game/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v037"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
rows=[]
for a in api.get_all_level_actors():
 label=a.get_actor_label()
 tags={str(t) for t in a.tags}
 if label=="CA_MW_PTA_PresentationShell_v014_FIXED_CM" or "HeavyFrame" in label or ("LB.PressTrain.ProcessDirection.PositiveY" in tags and any(s in label for s in ("S02","S03","S04","S05","S06"))):
  l=a.get_actor_location(); r=a.get_actor_rotation(); s=a.get_actor_scale3d(); row={"label":a.get_actor_label(),"location":[l.x,l.y,l.z],"rotation":[r.pitch,r.yaw,r.roll],"scale":[s.x,s.y,s.z]}
  if isinstance(a,unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
   b=a.static_mesh_component.static_mesh.get_bounds(); row["mesh_origin"]=[b.origin.x,b.origin.y,b.origin.z]; row["mesh_extent"]=[b.box_extent.x,b.box_extent.y,b.box_extent.z]
  rows.append(row)
print("LB_V037_ALIGNMENT "+json.dumps(rows,indent=2)); unreal.SystemLibrary.quit_editor()
