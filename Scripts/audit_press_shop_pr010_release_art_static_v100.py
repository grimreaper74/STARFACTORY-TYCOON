"""Exact-map import, authority, geometry and branding gate for PR-010 v100."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100"
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v100"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v100/pr010_release_art_static_gate_v100.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

actors = list(actors_api.get_all_level_actors())
scope = [actor for actor in actors if "LB.Station.PR010" in {str(tag) for tag in actor.tags}]
native = [actor for actor in scope if isinstance(actor, unreal.LBPR010Station)]
lane_beds = [actor for actor in scope if "lane_bed" in {str(tag) for tag in actor.tags}]
carriers = [actor for actor in scope if "carrier_position" in {str(tag) for tag in actor.tags}]
shuttles = [actor for actor in scope if "moving_infeed_shuttle" in {str(tag) for tag in actor.tags}]
panels = [actor for actor in scope if "LB.Safety.OpenMesh.GuardPanel" in {str(tag) for tag in actor.tags}]
proxies = [actor for actor in scope if "LB.PR010.CollisionProxy" in {str(tag) for tag in actor.tags}]
scanners = [actor for actor in scope if "LB.Safety.Scanner" in {str(tag) for tag in actor.tags}]
tow_points = [actor for actor in scope if "LB.Service.TowPoint" in {str(tag) for tag in actor.tags}]
hmis = [actor for actor in scope if actor.get_actor_label() == "LB_PR010_V100_RemoteCoordinationHMI"]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed.PR010.v100" in {str(tag) for tag in actor.tags}]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
v100_texts = [actor for actor in texts if actor.get_actor_label().startswith("LB_PR010_V100_TEXT_")]
text_content = [str(actor.text_render.get_editor_property("text")) for actor in texts]


def mesh_path(actor):
    component = getattr(actor, "static_mesh_component", None)
    value = component.get_editor_property("static_mesh") if component else None
    return value.get_path_name() if value else ""


def world_size(actor):
    _, extent = actor.get_actor_bounds(False, False)
    return [round(extent.x * 2, 3), round(extent.y * 2, 3), round(extent.z * 2, 3)]


failures = []
if len(native) != 1:
    failures.append(f"expected one native authority, found {len(native)}")
else:
    if native[0].get_actor_location().distance(unreal.Vector(1350, -2000, 0)) > 0.01:
        failures.append("native authority datum mismatch")
    if abs(native[0].get_actor_rotation().yaw + 90.0) > 0.01:
        failures.append("native authority yaw mismatch")
if len(lane_beds) != 4 or len(carriers) != 8:
    failures.append(f"lane/carrier cardinality mismatch {len(lane_beds)}/{len(carriers)}")
if len(shuttles) != 1 or abs(shuttles[0].get_actor_location().x - 1020.0) > 0.01:
    failures.append("moving cradle handoff datum/cardinality mismatch")
elif "InfeedTransferCradle_v100" not in mesh_path(shuttles[0]):
    failures.append("moving cradle does not use v100 imported mesh")
elif any(abs(value - expected) > 1.0 for value, expected in zip(world_size(shuttles[0]), (80, 240, 18))):
    failures.append(f"moving cradle world dimensions mismatch: {world_size(shuttles[0])}")
if len(panels) != 8:
    failures.append(f"expected eight v100 open-grid panels, found {len(panels)}")
for panel in panels:
    if "GuardPanel_OpenMesh_v100" not in mesh_path(panel):
        failures.append(f"wrong guard mesh: {panel.get_actor_label()}")
    if any(abs(value - expected) > 1.0 for value, expected in zip(world_size(panel), (8, 270, 120))):
        failures.append(f"guard dimensions mismatch: {panel.get_actor_label()} {world_size(panel)}")
    if panel.static_mesh_component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
        failures.append(f"visual guard has collision: {panel.get_actor_label()}")
if len(proxies) != 24:
    failures.append(f"expected 24 retained collision proxies, found {len(proxies)}")
if any(actor.static_mesh_component.get_editor_property("visible") for actor in proxies if hasattr(actor, "static_mesh_component")):
    failures.append("one or more retained guard collision proxies remain visible")
if len(scanners) != 4 or any("SafetyScanner_v100" not in mesh_path(actor) for actor in scanners):
    failures.append("four v100 safety scanners not installed")
if len(tow_points) != 4 or any("TowPoint_v100" not in mesh_path(actor) for actor in tow_points):
    failures.append("four v100 tow points not installed")
if len(hmis) != 1:
    failures.append(f"expected one v100 remote HMI, found {len(hmis)}")
else:
    hmi = hmis[0]
    if hmi.get_actor_location().distance(unreal.Vector(1025, -2645, 0)) > 0.01:
        failures.append("v100 HMI authoritative location mismatch")
    if "RemoteHMIHousing_v100" not in mesh_path(hmi):
        failures.append("v100 HMI mesh missing")
    if any(abs(value - expected) > 1.0 for value, expected in zip(world_size(hmi), (50, 76, 165))):
        failures.append(f"HMI world dimensions mismatch: {world_size(hmi)}")
if len(cameras) != 1:
    failures.append(f"expected one retargeted v100 HMI camera, found {len(cameras)}")
if len(v100_texts) != 3:
    failures.append(f"expected three v100 identity texts, found {len(v100_texts)}")
for required in ("CAIRNWELL AUTOMOTIVE", "MOORCROSS WORKS", "PR-010  FOUR-LANE BUFFER"):
    if not any(required in value for value in text_content):
        failures.append(f"missing diegetic identity: {required}")
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_content):
    failures.append("working-title branding found in-world")
if [actor.get_actor_label() for actor in scope if "PRESS TRAIN" in actor.get_actor_label().upper() or "PT-A" in actor.get_actor_label().upper()]:
    failures.append("press-train datum/actor was invented")

missing_assets = [name for name in (
    "SM_CA_MW_PR010_GuardPanel_OpenMesh_v100", "SM_CA_MW_PR010_InfeedTransferCradle_v100",
    "SM_CA_MW_PR010_RemoteHMIHousing_v100", "SM_CA_MW_PR010_SafetyScanner_v100",
    "SM_CA_MW_PR010_TowPoint_v100") if not library.does_asset_exist(f"{DEST}/{name}")]
if missing_assets:
    failures.append(f"missing imported assets: {missing_assets}")

report = {
    "$schema": "cairnwell/audit/pr010-release-art-static-v100/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V100_IMPORT_AUTHORITY_DIMENSIONS_OPEN_GUARDS_HMI_BRANDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V100_STATIC__NOT_PROMOTED",
    "map": MAP, "scope_actor_count": len(scope), "native_station_count": len(native),
    "lane_bed_count": len(lane_beds), "carrier_position_count": len(carriers),
    "open_guard_visual_count": len(panels), "hidden_collision_proxy_count": len(proxies),
    "scanner_count": len(scanners), "tow_point_count": len(tow_points), "hmi_count": len(hmis),
    "hmi_camera_count": len(cameras), "identity_text": text_content,
    "press_train_datums": "TBC_NOT_INVENTED", "missing_imported_assets": missing_assets,
    "failures": failures, "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
