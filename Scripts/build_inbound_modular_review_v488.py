"""Build an isolated fixed-camera review of inbound modular candidate v001.

This never loads or saves the retained press-shop map.
"""
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v489"
DEST = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
library = unreal.EditorAssetLibrary

if library.does_asset_exist(MAP):
    raise RuntimeError(f"Review map already exists; refusing overwrite: {MAP}")
if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create {MAP}")

def add(label, path, loc, rot=(0,0,0), scale=(1,1,1), tags=()):
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing review mesh: {path}")
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot))
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.static_mesh_component.set_static_mesh(mesh)
    a.tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted")] + [unreal.Name(t) for t in tags]
    return a

def mod(name, loc, rot=(0,0,0)):
    return add("LB_INBOUND_" + name, f"{DEST}/SM_CA_MW_MOD_{name}_v001", loc, rot)

# Vehicle and dock sequence, left-to-right in the review frame.
mod("LorryCab", (-900,-520,137), (0,0,0))
mod("CoilTrailer", (-900,150,188), (0,0,0))
mod("DockGuidesAndRestraint", (-900,150,35))
mod("DockControlAndSignals", (-620,630,125))
mod("ReceivingSaddle", (0,600,47))
mod("IdentityScanner", (260,620,93))
mod("AGVHandoffGuides", (550,600,18))

# Retained component families shown only for context/reuse proof.
add("LB_INBOUND_CoilAGV_Chassis",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001",
    (550,600,45), tags=("LB.Vehicle.CoilAGV",))
add("LB_INBOUND_CoilAGV_Deck",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001",
    (550,600,83), tags=("LB.Vehicle.CoilAGV.LiftDeck",))
add("LB_INBOUND_CraneGirder",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_BridgeGirder_4500_v001",
    (0,570,720), (0,0,90), (1.25,1,1))
add("LB_INBOUND_PoweredCHook",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035",
    (0,600,430), (0,0,0))

cube = "/Engine/BasicShapes/Cube.Cube"
floor = add("LB_INBOUND_ReviewFloor", cube, (0,100,-10), scale=(24,18,0.2))
floor.tags.append(unreal.Name("LB.Environment.ReviewOnly"))

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-38,-28,-18))
sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 3.0)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_properties({"intensity":1.0,"real_time_capture":True})
key = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-250,-100,900), unreal.Rotator())
key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(key.get_actor_location(), unreal.Vector(-100,250,100)), False)
key.rect_light_component.set_editor_properties({"intensity":1500.0,"attenuation_radius":3500.0,"source_width":900.0,"source_height":500.0})

pp = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
pp.set_editor_properties({"unbound":True,"blend_weight":1.0})
s = pp.settings
s.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,
 "override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,
 "auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,
 "override_auto_exposure_bias":True,"auto_exposure_bias":-1.3})
pp.settings = s

cam = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(2150,-2250,1450), unreal.Rotator())
cam.set_actor_label("LB_CAM_InboundCoilDelivery_v489")
cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(), unreal.Vector(-150,250,190)), False)
cam.camera_component.set_editor_properties({"field_of_view":50.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})
cam.tags = [unreal.Name("LB.Camera.Fixed"), unreal.Name("LB.Asset.ValidationOnly")]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving isolated inbound review map")
unreal.log("LINE_BOSS_INBOUND_REVIEW_V489_BUILD_PASS")
