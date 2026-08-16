import unreal
MAP='/Game/LineBoss/Developer/Validation/Maps/LB_S01_CleaningRobot_MaterialProof_v944'; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
for a in actors.get_all_level_actors():
 pc=a.get_component_by_class(unreal.PointLightComponent)
 if pc: pc.set_editor_property('intensity',650.0); pc.set_editor_property('attenuation_radius',900.0)
 dc=a.get_component_by_class(unreal.DirectionalLightComponent)
 if dc: dc.set_editor_property('intensity',2.0)
 sc=a.get_component_by_class(unreal.SkyLightComponent)
 if sc: sc.set_editor_property('intensity',0.65)
if not levels.save_current_level(): raise RuntimeError('save adjusted proof map failed')
unreal.log('LINE_BOSS_PROOF_LIGHTING_V945_PASS')
