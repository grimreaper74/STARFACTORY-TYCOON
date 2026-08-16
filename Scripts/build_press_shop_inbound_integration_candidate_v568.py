"""Fresh direct-v438 child: additive inbound coil-delivery presentation only.

The retained map-owned Coil AGV/controller and PR-003 storage remain authoritative.
This candidate adds the previously missing lorry/dock/crane/saddle presentation
upstream and deliberately does not add a second AGV or in-transfer coil.
"""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
SRC = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v568"
SRC_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_direct_v438_build_v568.json"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

before = hashlib.sha256(SRC_FILE.read_bytes()).hexdigest().upper()
if before != EXPECTED:
    raise RuntimeError(f"Protected v438 hash mismatch before build: {before}")
if not library.does_asset_exist(MAP):
    raise RuntimeError(f"Prepared candidate is missing: {MAP}")
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v568")

# v564 local process coordinates translated upstream of PR-003. The retained
# AGV stages near the handoff end; no duplicate vehicle/payload is spawned.
OFFSET = unreal.Vector(-11000.0, -2000.0, 0.0)
TAGS = [unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Inbound.ProPack.20260807"),
        unreal.Name("LB.Engineering.Values.TBC"),
        unreal.Name("LB.Inbound.DirectV438.v568")]

items = [
    ("LorryFourCoil", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v005/SM_CA_MW_Inbound_LorryFourCoil_v005", (-2200,0,0), -90),
    ("DockArchitecture", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v003/SM_CA_MW_Inbound_DockArchitecture_v003", (-3200,0,0), -90),
    ("DockGuidesRestraint", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_DockGuidesAndRestraint_v005", (-2350,0,35), -90),
    ("DockControlsSignals", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_DockControlAndSignals_v005", (-2850,720,0), -90),
    ("ProtectedEnclosure", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v002/SM_CA_MW_Inbound_InstalledEnclosure_v002", (0,0,0), 0),
    ("CraneRunway", "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v002/SM_CA_MW_InboundCrane_StaticRunwayFrame_v002", (0,0,0), 0),
    ("CraneBridge", "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v002/SM_CA_MW_InboundCrane_MovingBridge_v002", (0,0,652), 0),
    ("CraneTrolley", "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_Trolley_v001", (0,0,715), 0),
    ("HoistBlock", "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_HoistBlock_v001", (0,0,500), 0),
    ("PoweredCHook", "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035", (0,0,315), 90),
    ("ReceivingSaddle", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_ReceivingSaddle_v005", (750,0,70), 0),
    ("IdentityScanner", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_IdentityScanner_v005", (750,-260,93), 0),
    ("AGVHandoffGuides", "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_AGVHandoffGuides_v005", (1350,0,37), 0),
]

spawned = []
for short, path, local, yaw in items:
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing required mesh {path}")
    loc = OFFSET + unreal.Vector(*local)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, yaw))
    actor.set_actor_label(f"LB_INBOUND_V568_{short}")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.tags = TAGS + [unreal.Name(f"LB.Inbound.Module.{short}")]
    spawned.append({"label": actor.get_actor_label(), "asset": path,
                    "location_cm": [loc.x, loc.y, loc.z], "yaw": yaw})

# Fixed comparison cameras; existing gameplay cameras remain untouched.
for label, loc, target, fov in [
    ("LB_CAM_InboundIntegration_Process_v568", (-15300, 1200, 1350), (-11600,-2000,260), 52.0),
    ("LB_CAM_InboundIntegration_Handoff_v568", (-9800,800,900), (-11200,-2000,260), 48.0),
]:
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*loc), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16/9,
                                                    "constrain_aspect_ratio": True})
    camera.tags = TAGS + [unreal.Name("LB.Camera.FixedEvidence")]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v568")

after = hashlib.sha256(SRC_FILE.read_bytes()).hexdigest().upper()
if after != before:
    raise RuntimeError("Protected v438 changed during additive build")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "BUILT__VISUAL_AND_TECHNICAL_GATES_REQUIRED",
    "source_map": SRC, "candidate_map": MAP,
    "protected_v438_sha256_before": before, "protected_v438_sha256_after": after,
    "direct_child": True, "spawned_modules": spawned,
    "duplicate_coil_agv_spawned": False, "duplicate_in_transfer_coil_spawned": False,
    "runtime_authority_claimed": False, "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DIRECT_V438_BUILD_V568_PASS")
