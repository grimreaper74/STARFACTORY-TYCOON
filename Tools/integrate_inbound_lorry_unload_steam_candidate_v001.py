"""Restore the retained lorry-to-coil-inlet visual sequence in the Steam candidate.

The imported pieces are existing project-native inbound candidates, not new
Meshy generation.  The layout comes from the retained installed-cell audit
(v551) and is translated into the v438 receiving/front-end bays.  It is a
visual candidate only: no gameplay authority, save state, or protected map is
modified by this script.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
PROTECTED_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "inbound_lorry_unload_steam_candidate_v001.json"
TAG = unreal.Name("LB.PressShop.InboundLorry.SteamCandidate.v001")

# Local positions come from the retained v551 installed inbound cell.  This
# offset nests the dock in LB_ZONE_PRESS_RECEIVING and leads east through coil
# storage/front end toward the new five-station line.
ORIGIN = (-6000.0, -4300.0, 0.0)
ASSETS = {
    "Inbound lorry with four bright wrapped coils": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v003/SM_CA_MW_Inbound_LorryFourCoil_v003",
        (-2200.0, 0.0, 0.0),
    ),
    "Inbound dock architecture - retained": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v001/SM_CA_MW_Inbound_DockArchitecture_v001",
        (-3200.0, 0.0, 0.0),
    ),
    "Inbound dock guides and restraint - retained": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_DockGuidesAndRestraint_v005",
        (-2350.0, 0.0, 35.0),
    ),
    "Inbound dock controls - retained": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_DockControlAndSignals_v005",
        (-2650.0, -350.0, 125.0),
    ),
    "Inbound crane runway - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_StaticRunwayFrame_v001",
        (0.0, 0.0, 0.0),
    ),
    "Inbound crane moving bridge - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_MovingBridge_v001",
        (0.0, 0.0, 652.0),
    ),
    "Inbound crane trolley - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_Trolley_v001",
        (0.0, 0.0, 715.0),
    ),
    "Inbound powered C-hook - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035",
        (0.0, 0.0, 315.0),
    ),
    "Inbound C-hook carried coil - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
        (0.0, -50.0, 256.0),
    ),
    "Inbound receiving saddle - retained": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_ReceivingSaddle_v005",
        (750.0, 0.0, 70.0),
    ),
    "Inbound identity scanner - retained": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_IdentityScanner_v005",
        (750.0, -260.0, 93.0),
    ),
    "Inbound AGV handoff guides - retained": (
        "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_AGVHandoffGuides_v005",
        (1350.0, 0.0, 37.0),
    ),
    "Inbound coil AGV chassis - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001",
        (1350.0, 0.0, 45.0),
    ),
    "Inbound coil AGV deck - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001",
        (1350.0, 0.0, 83.0),
    ),
    "Inbound coil AGV loaded coil - retained": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
        (1350.0, 0.0, 185.0),
    ),
}


def fail(message):
    raise RuntimeError("INBOUND_LORRY_STEAM_CANDIDATE_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add(origin, local):
    return (origin[0] + local[0], origin[1] + local[1], origin[2] + local[2])


if not PROTECTED_FILE.is_file():
    fail("protected v438 source map is missing")
source_hash_before = sha256(PROTECTED_FILE)
if not unreal.EditorLoadingAndSavingUtils.load_map(CANDIDATE):
    fail("could not load Steam candidate map")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("inbound lorry candidate is already placed; refusing duplicates")

placed = []
for label, (path, local) in ASSETS.items():
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        fail("missing retained inbound mesh: " + label)
    location = add(ORIGIN, local)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.PressShop.NativeInbound"), unreal.Name("LB.Asset.Candidate"), unreal.Name("LB.NotProcessWIP")]
    actor.static_mesh_component.set_static_mesh(mesh)
    placed.append({"label": label, "asset": mesh.get_path_name(), "location_cm": list(location)})

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save Steam candidate map")
source_hash_after = sha256(PROTECTED_FILE)
if source_hash_before != source_hash_after:
    fail("protected v438 source map changed during candidate inbound placement")

report = {
    "status": "PASS__RETAINED_LORRY_UNLOAD_VISUAL_SEQUENCE_PLACED_IN_STEAM_CANDIDATE_ONLY",
    "candidate": CANDIDATE,
    "protected_v438_sha256_before": source_hash_before,
    "protected_v438_sha256_after": source_hash_after,
    "retained_reference": "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v548",
    "sequence": ["bright four-coil lorry", "dock/restraint", "bridge crane + powered C-hook", "receiving saddle", "loaded coil AGV", "front-end press inlet"],
    "placement_origin_cm": list(ORIGIN),
    "placed_actors": placed,
    "honest_status": "candidate presentation only; no actor is connected to gameplay delivery, save, collision, navigation, or build authority by this script",
    "next_gate": "visually inspect the combined lorry-to-new-press-line composition in full Unreal before adding any lights, camera actors, or further art",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("INBOUND_LORRY_STEAM_CANDIDATE=" + json.dumps({"placed": len(placed)}, sort_keys=True))
