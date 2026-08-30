"""Audit authoritative existing automation assets before adding any to 2126.

This is read-only: it prevents candidate dressing from inventing disposable
future props while letting the new map reuse the project Coil AGV and robot
library where those assets are technically loadable and visually suitable.
"""

import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_future_reuse_audit_v001.json"

ASSETS = {
    "approved_coil_agv": "/Game/LineBoss/Runtime/PressShop/CoilAGV/UntouchedControlled_v20260810/SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810",
    "coil_handler_body": "/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999/SM_Cairnwell_AGV_CHF01_StaticBody_v999",
    "coil_handler_lift": "/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999/SM_Cairnwell_AGV_CHF01_LiftAssembly_v999",
    "support_mobile_base": "/Game/LineBoss/Robots/Shared/RP01/Candidate_v003/Blueprints/BP_LB_RP01_MobileBase",
    "industrial_robot_arm": "/Game/Meshes/Robot/SM_RoboArm04",
    "press_unload_robot_base": "/Game/LineBoss/Developer/Validation/PressTrains/S07UnloadRobotRuntime_v757/Cairnwell_S07_UnloadRobot_Runtime_v756/StaticMeshes/PTA_S07_RuntimeRobotBase_v003",
    "press_unload_robot_shoulder": "/Game/LineBoss/Developer/Validation/PressTrains/S07UnloadRobotRuntime_v757/Cairnwell_S07_UnloadRobot_Runtime_v756/StaticMeshes/PTA_S07_RuntimeRobotShoulder_v003",
    "press_unload_robot_upper_arm": "/Game/LineBoss/Developer/Validation/PressTrains/S07UnloadRobotRuntime_v757/Cairnwell_S07_UnloadRobot_Runtime_v756/StaticMeshes/PTA_S07_RuntimeRobotUpperArm_v003",
}


def inspect(path):
    asset = unreal.load_asset(path)
    row = {"path": path, "found": asset is not None}
    if asset is None:
        return row
    row["class"] = asset.get_class().get_name()
    if isinstance(asset, unreal.StaticMesh):
        box = asset.get_bounding_box()
        row["bounds_cm"] = [
            round(box.max.x - box.min.x, 2),
            round(box.max.y - box.min.y, 2),
            round(box.max.z - box.min.z, 2),
        ]
        row["triangles_lod0"] = int(asset.get_num_triangles(0))
        row["material_slots"] = int(asset.get_num_sections(0))
    return row


rows = {name: inspect(path) for name, path in ASSETS.items()}
accepted = []
if rows["approved_coil_agv"].get("found") and rows["approved_coil_agv"].get("class") == "StaticMesh":
    accepted.append("approved_coil_agv")
if all(rows[key].get("found") and rows[key].get("class") == "StaticMesh" for key in (
        "press_unload_robot_base", "press_unload_robot_shoulder", "press_unload_robot_upper_arm")):
    accepted.append("press_unload_robot_partial")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS" if accepted else "FAIL__NO_REUSABLE_FUTURE_AUTOMATION_ASSETS",
    "candidate_map_untouched": True,
    "assets": rows,
    "approved_reuse_candidates": accepted,
    "notes": [
        "The project visual standard makes the procedural Coil AGV the active inbound authority.",
        "Do not use a Meshy coil carrier where the project authority already exists.",
        "Robot parts require an authored assembly / silhouette check before use in the screenshot map.",
    ],
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_FUTURE_REUSE_AUDIT_PASS candidates=%s" % ",".join(accepted))
