"""Exact-map static, identity, import and preserved-contract gate for PR-010 v103."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103"
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v103/pr010_release_art_static_gate_v103.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())
scope = [actor for actor in actors if "LB.Station.PR010" in {str(tag) for tag in actor.tags}]


def tags(actor):
    return {str(tag) for tag in actor.tags}


def bounds_size(actor):
    _, extent = actor.get_actor_bounds(False, False)
    return [round(value * 2, 3) for value in (extent.x, extent.y, extent.z)]


def near_size(actor, expected, tolerance=1.0):
    return all(abs(value - target) <= tolerance for value, target in zip(bounds_size(actor), expected))


native = [actor for actor in scope if isinstance(actor, unreal.LBPR010Station)]
carriers = [actor for actor in scope if "carrier_position" in tags(actor)]
stacks = [actor for actor in scope if "identified_blank_stack" in tags(actor) or "quality_hold_stack" in tags(actor)]
guards = [actor for actor in scope if "LB.Safety.OpenMesh.GuardPanel" in tags(actor)]
proxies = [actor for actor in scope if "LB.PR010.CollisionProxy" in tags(actor)]
v102_service = [actor for actor in scope if "LB.Asset.Candidate.v102" in tags(actor) and any(tag.startswith("LB.PR010.ServiceDeck.") for tag in tags(actor))]
service_banks = [actor for actor in scope if "LB.PR010.ServiceDeck.InstalledRouting" in tags(actor)]
access_hatches = [actor for actor in scope if "LB.PR010.ServiceDeck.AccessDetail" in tags(actor)]
plates = [actor for actor in scope if "LB.PR010.StackIdentityPlate" in tags(actor)]
primary_text = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor) and "LB.PR010.StackPositionID.v103" in tags(actor)]
reverse_text = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor) and "LB.PR010.StackPositionID.Reverse.v103" in tags(actor)]
stack_camera = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Evidence.StackID" in tags(actor)]
lights = [actor for actor in scope if isinstance(actor, unreal.PointLight) and "LB.PR010.Lighting.Calibrated.v103" in tags(actor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
text_content = [str(actor.text_render.get_editor_property("text")) for actor in texts]
failures = []
if len(native) != 1:
    failures.append(f"expected one native PR010 authority, found {len(native)}")
else:
    if native[0].get_actor_location().distance(unreal.Vector(1350, -2000, 0)) > 0.01:
        failures.append("native authority datum mismatch")
    if abs(native[0].get_actor_rotation().yaw + 90.0) > 0.01:
        failures.append("native authority yaw mismatch")
if len(carriers) != 8 or len(stacks) != 9 or len(guards) != 8:
    failures.append(f"retained carrier/stack/guard cardinality mismatch {len(carriers)}/{len(stacks)}/{len(guards)}")
if len(proxies) != 52:
    failures.append(f"expected 52 retained collision proxies, found {len(proxies)}")
if len(v102_service) != 16:
    failures.append(f"expected sixteen retained v102 service visuals, found {len(v102_service)}")
if len(service_banks) != 4 or any(not near_size(actor, (58.8, 270.0, 106.0)) for actor in service_banks):
    failures.append(f"v103 service-bank cardinality/dimensions failed: {len(service_banks)} {[bounds_size(actor) for actor in service_banks]}")
if len(access_hatches) != 4 or any(not near_size(actor, (13.05, 270.0, 65.0)) for actor in access_hatches):
    failures.append(f"v103 access-hatch cardinality/dimensions failed: {len(access_hatches)} {[bounds_size(actor) for actor in access_hatches]}")
if len(plates) != 9 or any(not near_size(actor, (90.0, 8.0, 32.0)) for actor in plates):
    failures.append(f"v103 stack plate cardinality/dimensions failed: {len(plates)} {[bounds_size(actor) for actor in plates]}")
if any(actor.static_mesh_component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION for actor in service_banks + access_hatches + plates):
    failures.append("one or more v103 presentation modules have collision enabled")
if len(primary_text) != 9 or any(actor.text_render.get_editor_property("visible") for actor in primary_text):
    failures.append("nine hidden forward stack texts were not preserved as the non-rendering side")
if len(reverse_text) != 9 or any(not actor.text_render.get_editor_property("visible") for actor in reverse_text):
    failures.append("nine visible camera-facing stack texts were not installed")
if len(stack_camera) != 1:
    failures.append(f"expected one fixed stack-ID evidence camera, found {len(stack_camera)}")
expected_lights = sorted((65.0, 95.0, 95.0, 105.0))
actual_lights = sorted(round(actor.point_light_component.get_editor_property("intensity"), 3) for actor in lights)
if len(lights) != 4 or actual_lights != expected_lights:
    failures.append(f"v103 calibrated light contract mismatch: {actual_lights}")
required_assets = (
    "SM_CA_MW_PR010_InstalledServiceBank_v103",
    "SM_CA_MW_PR010_ServiceAccessHatchSection_v103",
    "SM_CA_MW_PR010_StackIdentityPlate_v103",
    "Materials/M_CA_MW_PR010_StackLabel_v103",
)
missing_assets = [name for name in required_assets if not library.does_asset_exist(f"{DEST}/{name}")]
if missing_assets:
    failures.append(f"missing v103 assets: {missing_assets}")
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_content):
    failures.append("working-title branding found in PR010 text")
invented_train_actors = [actor.get_actor_label() for actor in scope if "PRESS TRAIN" in actor.get_actor_label().upper() or "PT-A" in actor.get_actor_label().upper()]
if invented_train_actors:
    failures.append(f"press-train datum/actor invented: {invented_train_actors}")
report = {
    "$schema": "cairnwell/audit/pr010-release-art-static-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V103_EXACT_MAP_AUTHORITY_RETAINED_COLLISION_INSTALLED_SERVICE_STACK_LABEL_LIGHT_BRANDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V103_STATIC__NOT_PROMOTED",
    "map": MAP, "scope_actor_count": len(scope), "native_station_count": len(native),
    "carrier_count": len(carriers), "stack_count": len(stacks), "open_guard_count": len(guards),
    "collision_proxy_count": len(proxies), "retained_v102_service_visual_count": len(v102_service),
    "v103_service_bank_count": len(service_banks), "v103_access_hatch_count": len(access_hatches),
    "v103_stack_plate_count": len(plates), "visible_stack_text_count": len(reverse_text),
    "stack_id_camera_count": len(stack_camera), "calibrated_light_intensities": actual_lights,
    "missing_assets": missing_assets, "press_train_datums": "TBC_NOT_INVENTED",
    "failures": failures, "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
