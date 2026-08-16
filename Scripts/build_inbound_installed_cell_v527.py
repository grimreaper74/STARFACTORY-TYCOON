"""Fresh v527 compact linear installation around retained enclosure v001."""
from pathlib import Path
import unreal

root=Path(__file__).parent
source=(root/'build_inbound_installed_cell_v526.py').read_text(encoding='utf-8')
source=source.replace('v526','v527').replace('V526','V527').replace('V026_','V027_')
exec(compile(source,str(root/'build_inbound_installed_cell_v526.py'),'exec'),globals(),globals())

actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def find(suffix):
    return next((a for a in actors.get_all_level_actors() if a.get_actor_label().endswith(suffix)),None)
def place(suffix,loc,yaw=None):
    a=find(suffix)
    if a is None: raise RuntimeError(f'Missing v527 actor {suffix}')
    a.set_actor_location(unreal.Vector(*loc),False,False)
    if yaw is not None: a.set_actor_rotation(unreal.Rotator(0,0,yaw),False)
    return a

# Compact, continuous material-flow spine.  Trailer sits partly beneath the
# protected crane bay as on the owner sheets; set-down and AGV continue right.
place('LorryCab',(-1460,0,152),90)
place('CoilTrailer',(-560,0,188),-90)
place('DockGuidesAndRestraint',(-560,0,35),-90)
place('EntranceDockEnvelope',(-1240,0,244),-90)
place('DockControlAndSignals',(-1010,-350,125),-90)
for suffix,loc,yaw in (
    ('StaticRunwayFrame',(120,0,0),0),('MovingBridge',(120,0,652),0),
    ('CraneTrolley',(120,0,715),0),('HoistBlock',(120,0,500),0),
    ('PoweredCHook',(120,0,315),90),('CHook_CarriedCoil',(120,-50,256),0),
    ('PurposeBuiltInstalledEnclosure',(120,0,0),0),
    ('ReceivingSaddle',(850,0,70),0),('IdentityScanner',(850,-260,93),0),
    ('AGVHandoffGuides',(1370,0,37),0),('AGV_Chassis',(1370,0,45),0),
    ('AGV_Deck',(1370,0,83),0),('AGV_LoadedCoil',(1370,0,185),0)):
    place(suffix,loc,yaw)

# Side-elevation process camera establishes true left-to-right readability.
overview=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='LB_CAM_InboundHall_ProcessOverview_v527')
overview.set_actor_location(unreal.Vector(0,-5700,1750),False,False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(),unreal.Vector(0,0,300)),False)
overview.camera_component.set_editor_property('field_of_view',50.0)
hero=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='LB_CAM_InboundHall_CraneHero_v527')
hero.set_actor_location(unreal.Vector(150,-3600,1325),False,False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location(),unreal.Vector(150,0,350)),False)
hero.camera_component.set_editor_property('field_of_view',52.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError('Failed saving v527 compact installed cell')
unreal.log('LINE_BOSS_INBOUND_COMPACT_LINEAR_V527_BUILD_PASS')
