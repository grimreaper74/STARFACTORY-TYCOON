"""Add the validated inbound unloading presentation to clean press-shop v767.

Creates a fresh successor map, expands only the clean authored hall shell, and
installs the accepted lorry/dock/crane/handoff modules. It never opens the
protected v438 map for editing and does not import any legacy press actors.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

SRC = "/Game/LineBoss/Maps/LB_PressShop_Trains_S01_S07_v767"
MAP = "/Game/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770"
PROJECT = Path(unreal.Paths.project_dir()).resolve()
PROTECTED = PROJECT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/clean_press_shop_inbound_build_v770.json"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()

protected_before = sha256(PROTECTED)
if protected_before != EXPECTED:
    raise RuntimeError(f"Protected v438 mismatch before build: {protected_before}")
if lib.does_asset_exist(MAP):
    raise RuntimeError(f"Fresh-map invariant failed: {MAP}")
if not levels.new_level_from_template(MAP, SRC):
    raise RuntimeError(f"Could not create {MAP} from {SRC}")

by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}

# Expand the clean v720-authored shell westwards, preserving the east wall and
# the four widened train datums. Floor remains at Z=0 and width is unchanged.
shell_changes = []
for label in ("LB_NEW_Floor_Main", "LB_NEW_Wall_North", "LB_NEW_Wall_South"):
    actor = by_label.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError(f"Missing clean shell actor {label}")
    old_loc = actor.get_actor_location()
    old_scale = actor.get_actor_scale3d()
    actor.set_actor_location(unreal.Vector(-2500.0, old_loc.y, old_loc.z), False, False)
    actor.set_actor_scale3d(unreal.Vector(270.0, old_scale.y, old_scale.z))
    actor.tags = list(actor.tags) + [unreal.Name("LB.Environment.CleanWestBayExpansion.v770")]
    shell_changes.append(label)
west = by_label.get("LB_NEW_Wall_West")
if not isinstance(west, unreal.StaticMeshActor):
    raise RuntimeError("Missing clean west wall")
west.set_actor_location(unreal.Vector(-16000.0, -1000.0, 700.0), False, False)
west.tags = list(west.tags) + [unreal.Name("LB.Environment.CleanWestBayExpansion.v770")]
shell_changes.append(west.get_actor_label())

OFFSET = unreal.Vector(-12000.0, -2000.0, 0.0)
BASE_TAGS = [
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Inbound.ProPack.20260807"),
    unreal.Name("LB.Inbound.CleanMap.v770"),
]
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

installed = []
for short, path, local, yaw in items:
    mesh = lib.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing accepted inbound mesh {path}")
    loc = OFFSET + unreal.Vector(*local)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, yaw))
    actor.set_actor_label(f"LB_INBOUND_V770_{short}")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.tags = BASE_TAGS + [unreal.Name(f"LB.Inbound.Module.{short}")]
    installed.append({"label": actor.get_actor_label(), "asset": path,
                      "location_cm": [loc.x, loc.y, loc.z], "yaw": yaw})

# Exact accepted wrapped-coil identity from the v616 audit, now on the clean map.
coil_mesh_path = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
coil_mesh = lib.load_asset(coil_mesh_path)
if not isinstance(coil_mesh, unreal.StaticMesh):
    raise RuntimeError("Missing accepted wrapped master coil")
coils = []
for idx, x in enumerate((-15760.0, -15520.0, -15280.0, -15040.0), 1):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, -2000.0, 152.0), unreal.Rotator())
    actor.set_actor_label(f"LB_INBOUND_V770_TrailerWrappedCoil_{idx:02d}")
    actor.static_mesh_component.set_static_mesh(coil_mesh)
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    actor.tags = BASE_TAGS + [unreal.Name(f"LB.Inbound.Visual.TrailerCoil.{idx:02d}")]
    coils.append(actor.get_actor_label())

for label, loc, target, fov in [
    ("LB_CAM_InboundClean_Process_v770", (-15700, 1800, 1350), (-12300,-2000,260), 52.0),
    ("LB_CAM_InboundClean_Handoff_v770", (-10200,900,900), (-11900,-2000,260), 48.0),
    ("LB_CAM_InboundClean_WholeShop_v770", (-5000,3900,1900), (-2500,-1000,250), 58.0),
]:
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*loc), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16/9,
                                                    "constrain_aspect_ratio": True})
    camera.tags = BASE_TAGS + [unreal.Name("LB.Camera.FixedEvidence")]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Could not save v770")
protected_after = sha256(PROTECTED)
if protected_after != protected_before:
    raise RuntimeError("Protected v438 changed")

map_file = PROJECT / "Content/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770.umap"
payload = {
    "$schema": "cairnwell/audit/clean-press-shop-inbound-build-v770/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CLEAN_MAP_INBOUND_VISUAL_INSTALLED__FUNCTIONAL_GATES_OPEN__NOT_PROMOTED",
    "source_map": SRC,
    "candidate_map": MAP,
    "map_sha256": sha256(map_file),
    "shell_changes": shell_changes,
    "installed_modules": installed,
    "wrapped_coils": coils,
    "legacy_press_actors_imported": False,
    "legacy_unload_robot_imported": False,
    "meshy_credits_used": 0,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_PRESS_SHOP_INBOUND_BUILD_V770_PASS")
