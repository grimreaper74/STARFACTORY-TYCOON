import unreal
MAP='/Game/LineBoss/Developer/Validation/Maps/LB_S01_CleaningRobot_MaterialProof_v944'; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
hits=[a for a in actors.get_all_level_actors() if a.get_actor_label()=='LB_PROOF_CLEANING_ROBOT_v942']
if len(hits)!=1:raise RuntimeError(f'cleaning robot actor resolution {hits}')
a=hits[0];o,e=a.get_actor_bounds(False);floor_z=o.z-e.z;loc=a.get_actor_location();a.set_actor_location(unreal.Vector(loc.x,loc.y,loc.z-floor_z),False,False);o2,e2=a.get_actor_bounds(False);floor2=o2.z-e2.z
if abs(floor2)>0.2:raise RuntimeError(f'grounding failed minZ {floor2}')
if not levels.save_current_level():raise RuntimeError('save failed')
unreal.log(f'LINE_BOSS_CLEANING_ROBOT_GROUNDED_V946_PASS offset={-floor_z:.3f} minZ={floor2:.3f}')
