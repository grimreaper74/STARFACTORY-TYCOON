"""Fresh v526 review: purpose-built enclosure around retained inbound process."""
from pathlib import Path
import unreal

root=Path(__file__).parent
source=(root/'build_inbound_installed_cell_v524.py').read_text(encoding='utf-8')
source=source.replace('v524','v526').replace('V524','V526').replace('V024_','V026_')
exec(compile(source,str(root/'build_inbound_installed_cell_v524.py'),'exec'),globals(),globals())

library=unreal.EditorAssetLibrary
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
enclosure=library.load_asset('/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v001/SM_CA_MW_Inbound_InstalledEnclosure_v001')
if not isinstance(enclosure,unreal.StaticMesh): raise RuntimeError('Missing imported purpose-built enclosure')
a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0),unreal.Rotator())
a.set_actor_label('LB_INBOUND_V026_PurposeBuiltInstalledEnclosure')
a.static_mesh_component.set_static_mesh(enclosure)
a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
a.static_mesh_component.set_editor_property('can_ever_affect_navigation',True)
a.tags=[unreal.Name('LB.Asset.ValidationOnly'),unreal.Name('LB.Asset.CandidateNotPromoted'),unreal.Name('LB.Engineering.Values.TBC')]

# Extend the installed floor to carry the whole lorry and handoff sequence.
floor=next(x for x in actors.get_all_level_actors() if x.get_actor_label().endswith('Floor'))
floor.set_actor_scale3d(unreal.Vector(32,23,.24))

overview=next(x for x in actors.get_all_level_actors() if x.get_actor_label()=='LB_CAM_InboundHall_ProcessOverview_v526')
overview.set_actor_location(unreal.Vector(3900,-4550,2050),False,False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(),unreal.Vector(-350,0,260)),False)
overview.camera_component.set_editor_property('field_of_view',60.0)
hero=next(x for x in actors.get_all_level_actors() if x.get_actor_label()=='LB_CAM_InboundHall_CraneHero_v526')
hero.set_actor_location(unreal.Vector(-700,-3350,1450),False,False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location(),unreal.Vector(-100,0,350)),False)
hero.camera_component.set_editor_property('field_of_view',55.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError('Failed saving v526 enclosed inbound cell')
unreal.log('LINE_BOSS_INBOUND_ENCLOSED_CELL_V526_BUILD_PASS')
