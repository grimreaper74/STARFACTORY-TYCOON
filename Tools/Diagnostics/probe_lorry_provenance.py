"""Report every material a candidate dock vehicle mesh binds, and flag any that
trips the OneFactory provenance rule.

ALBOneFactoryBootstrap::ActorUsesForbiddenProvenance rejects an actor whose name,
tags, mesh path or ANY bound material path contains 'Meshy' or
'ExternalGenerated'. Nine site lorries placed as saved level actors bound
M_CA_MW_Lorry_MeshyPBR_v006 and locked the whole factory out of commissioning,
so pick the replacement by measurement rather than by asset name.
"""
import io
import json
import os

import unreal

OUT = os.environ.get("LB_LORRY_OUT", "C:/Temp/lb_lorry.json")
FORBIDDEN = ("meshy", "externalgenerated")

CANDIDATES = [
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/"
    "SM_CA_MW_InboundLorry_Approved_v006",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/"
    "SM_CA_MW_MOD_LorryCab_v005",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/"
    "SM_CA_MW_MOD_CoilTrailer_v005",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v005/"
    "SM_CA_MW_Inbound_LorryFourCoil_v005",
    "/Game/Meshes/Truck/SM_Truck_cabin_01",
    "/Game/Meshes/Truck/SM_Truck_frame_01",
    "/Game/Meshes/Truck/SM_Truck_tank_01",
    "/Game/Meshes/CargoCar/SM_CargoCart01",
    "/Game/Meshes/SM_Container01_01",
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Fence_01",
    "/Game/Meshes/SM_GateDoor01",
    "/Game/Meshes/SM_Background2_Hangar",
    "/Game/Meshes/SM_Background1_Tower01",
    "/Game/Meshes/SM_CrashAreaSpotlight_01",
    "/Game/Meshes/SM_ConcreteWall",
    "/Game/Meshes/SM_ConcretePillar01",
    "/Game/Meshes/SM_Background2_BoxBuilding",
    "/Game/Meshes/SM_Background2_BoxBuildingBase",
    "/Game/Meshes/SM_ContainerP4_01",
    "/Game/Meshes/SM_Container01_02",
    "/Game/Meshes/SM_Background1_Tower02",
    "/Game/Meshes/SM_Background1_Tower03",
    "/Game/Meshes/SM_Background1_Tower04",
    "/Game/Meshes/SM_Background1_AntennaTower",
    "/Game/Meshes/SM_GateBorder01",
    "/Engine/BasicShapes/Plane",
]


def offending(path):
    lowered = path.lower()
    return [token for token in FORBIDDEN if token in lowered]


report = []
for path in CANDIDATES:
    mesh = unreal.load_asset(path)
    if mesh is None:
        report.append({"mesh": path, "missing": True})
        continue
    materials = []
    bad = list(offending(path))
    for slot in mesh.static_materials:
        interface = slot.material_interface
        material_path = interface.get_path_name() if interface else "<none>"
        materials.append(material_path)
        bad.extend(offending(material_path))
    report.append({
        "mesh": path.rsplit("/", 1)[-1],
        "path": path,
        "materials": materials,
        "forbidden": sorted(set(bad)),
        "safe": not bad,
    })

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1))
unreal.log("LINE_BOSS_LORRY_PROBE {} candidates, {} unsafe -> {}".format(
    len(report), sum(1 for r in report if not r.get("safe", True)), OUT))
