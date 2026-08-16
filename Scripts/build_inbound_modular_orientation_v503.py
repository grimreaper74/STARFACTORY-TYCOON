"""Build isolated installed-context review for inbound Modular_v003."""
import unreal
MAP="/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryOrientation_v503";DEST="/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v003";BRIDGE="/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);library=unreal.EditorAssetLibrary
if library.does_asset_exist(MAP):raise RuntimeError(f"Refusing overwrite {MAP}")
if not levels.new_level(MAP):raise RuntimeError("Could not create v503")
def add(label,path,loc,rot=(0,0,0),scale=(1,1,1),tags=()):
 mesh=library.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"Missing {path}")
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(*rot));a.set_actor_label(label);a.set_actor_scale3d(unreal.Vector(*scale));a.static_mesh_component.set_static_mesh(mesh);a.tags=[unreal.Name("LB.Asset.ValidationOnly"),unreal.Name("LB.Asset.CandidateNotPromoted")]+[unreal.Name(t) for t in tags];return a
def mod(name,loc,rot=(0,0,0)):return add("LB_INBOUND_V003_"+name,f"{DEST}/SM_CA_MW_MOD_{name}_v003",loc,rot)
mod("LorryCab",(0,-885,152),rot=(0,0,180));mod("CoilTrailer",(0,-150,188));mod("DockGuidesAndRestraint",(0,-150,35));mod("EntranceDockEnvelope",(0,-665,244));mod("DockControlAndSignals",(-310,-500,125));mod("CraneBayStructure",(0,700,320));mod("ReceivingSaddle",(0,700,47));mod("IdentityScanner",(240,700,93));mod("AGVHandoffGuides",(420,850,18))
add("LB_INBOUND_V003_AGV_Chassis","/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001",(420,850,45),tags=("LB.Vehicle.CoilAGV",))
add("LB_INBOUND_V003_AGV_Deck","/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001",(420,850,83),tags=("LB.Vehicle.CoilAGV.LiftDeck",))
yellow=library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001")
girder=add("LB_INBOUND_V003_CraneGirder",f"{BRIDGE}/SM_LB_Crane_BridgeGirder_4500_v001",(0,700,610),scale=(1.42,1,1))
trolley=add("LB_INBOUND_V003_CraneTrolley",f"{BRIDGE}/SM_LB_Crane_Trolley_v001",(0,500,625))
hoist=add("LB_INBOUND_V003_HoistBlock",f"{BRIDGE}/SM_LB_Crane_HoistBlock_v001",(0,500,500))
hook=add("LB_INBOUND_V003_PoweredCHook",f"{BRIDGE}/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035",(0,500,315),rot=(0,0,90))
for crane_actor in (girder,trolley,hoist,hook):
 for index in range(crane_actor.static_mesh_component.get_num_materials()): crane_actor.static_mesh_component.set_material(index,yellow)
floor=add("LB_INBOUND_V003_Floor","/Engine/BasicShapes/Cube.Cube",(0,100,-12),scale=(18,28,.24),tags=("LB.Environment.ReviewOnly",));concrete=library.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete");floor.static_mesh_component.set_material(0,concrete)
steel=library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_BrushedSteel_v001")
charcoal=library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001")
back=add("LB_INBOUND_V003_Backdrop","/Engine/BasicShapes/Cube.Cube",(0,1650,380),scale=(18,.18,7.6),tags=("LB.Environment.ReviewOnly",));back.static_mesh_component.set_material(0,steel)
for x in (-750,-375,0,375,750):
 column=add("LB_INBOUND_V003_BackdropColumn_"+str(x),"/Engine/BasicShapes/Cube.Cube",(x,1550,390),scale=(.18,.18,7.8),tags=("LB.Environment.ReviewOnly",));column.static_mesh_component.set_material(0,charcoal)
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(),unreal.Rotator(-35,-25,-18));sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity",3.0)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(),unreal.Rotator());sky.get_component_by_class(unreal.SkyLightComponent).set_editor_properties({"intensity":1.1,"real_time_capture":True})
key=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(-500,-200,1200),unreal.Rotator());key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(key.get_actor_location(),unreal.Vector(0,250,180)),False);key.rect_light_component.set_editor_properties({"intensity":2200.0,"attenuation_radius":4000.0,"source_width":1000.0,"source_height":600.0})
pp=actors.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(),unreal.Rotator());pp.set_editor_properties({"unbound":True,"blend_weight":1.0});s=pp.settings;s.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":-1.1});pp.settings=s
cam=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-2050,-2450,1350),unreal.Rotator());cam.set_actor_label("LB_CAM_InboundCoilDelivery_Orientation_v503");cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(0,180,200)),False);cam.camera_component.set_editor_properties({"field_of_view":55.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True});cam.tags=[unreal.Name("LB.Camera.Fixed"),unreal.Name("LB.Asset.ValidationOnly")]
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Failed saving v503")
unreal.log("LINE_BOSS_INBOUND_ORIENTATION_V503_BUILD_PASS")
