"""Supplemental current-state verification of control, inspection and dispatch.

Run after structural v003: this confirms the final three readable process
states were added with real reusable assets. It does not replace the still-open
live-editor screenshot acceptance gate.
"""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_endpoint_validation_v004.json"
HMI = "/Game/LineBoss/Candidates/PressShop/OperatorHMIStand_v001/SM_LB_OperatorHMIStand_v001"
ENDPOINTS = {
    "OUTBOUND | real vision inspection gate": "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001",
    "OUTBOUND | inspected panel stillage": "/Game/LineBoss/Candidates/PressTrains/Shared/ExteriorDetail_v002/SM_CA_MW_PT_S07InspectionStillageDress_v002",
    "OUTBOUND | real dunnage dispatch": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001",
}
HMIS = {"CONTROL | S02 Draw operator HMI", "CONTROL | S03 Trim operator HMI", "CONTROL | S04 Pierce operator HMI", "CONTROL | S05 Flange operator HMI", "CONTROL | S06 Vision operator HMI"}


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_ENDPOINT_VALIDATION_V004_FAIL: " + message)


def visible(actor):
    return all(component.is_visible() for component in actor.get_components_by_class(unreal.PrimitiveComponent))


def static_path(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("actor is not StaticMeshActor: " + actor.get_actor_label())
    mesh = actor.static_mesh_component.static_mesh
    if not isinstance(mesh, unreal.StaticMesh):
        fail("actor has no static mesh: " + actor.get_actor_label())
    return mesh.get_path_name().split(".")[0], mesh


if not unreal.EditorAssetLibrary.does_asset_exist(MAP) or not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("fresh candidate map unavailable")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
hmi_rows = []
for label in sorted(HMIS):
    actor = by_label.get(label)
    if actor is None or not visible(actor):
        fail("missing or hidden functional HMI: " + label)
    actual, mesh = static_path(actor)
    if actual != HMI:
        fail("wrong HMI mesh: " + label)
    hmi_rows.append({"label": label, "triangles_lod0": int(mesh.get_num_triangles(0))})

endpoint_rows = []
for label, expected in ENDPOINTS.items():
    actor = by_label.get(label)
    if actor is None or not visible(actor):
        fail("missing or hidden endpoint: " + label)
    actual, mesh = static_path(actor)
    if actual != expected:
        fail("wrong endpoint mesh: " + label)
    endpoint_rows.append({"label": label, "triangles_lod0": int(mesh.get_num_triangles(0))})

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CONTROLS_INSPECTION_AND_DISPATCH_CURRENTLY_PRESENT_IN_FRESH_2126_CANDIDATE",
    "candidate_map": MAP,
    "candidate_actor_count": len(actors),
    "operator_hmis": hmi_rows,
    "inspection_and_dispatch": endpoint_rows,
    "honest_status": "structural current-state evidence only; live-editor screenshot review is still mandatory",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ENDPOINT_VALIDATION_V004_PASS hmis=%d endpoints=%d" % (len(hmi_rows), len(endpoint_rows)))
