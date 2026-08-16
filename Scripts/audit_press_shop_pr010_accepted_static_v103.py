"""Post-promotion exact-map static and immutable-tag gate for PR-010 v103."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103"
OUT = ROOT / "Saved/Audits/PR010_Accepted_v103/accepted_static_audit.json"
ACCEPTED_TAG = "LB.Asset.Accepted.PR010.v103"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())


def tags(actor):
    return {str(tag) for tag in actor.tags}


def size(actor):
    _, extent = actor.get_actor_bounds(False, False)
    return tuple(round(value * 2, 3) for value in (extent.x, extent.y, extent.z))


scope = [actor for actor in actors if "LB.Station.PR010" in tags(actor)]
native = [actor for actor in scope if isinstance(actor, unreal.LBPR010Station)]
pr009_native = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
carriers = [actor for actor in scope if "carrier_position" in tags(actor)]
stacks = [actor for actor in scope if "identified_blank_stack" in tags(actor) or "quality_hold_stack" in tags(actor)]
guards = [actor for actor in scope if "LB.Safety.OpenMesh.GuardPanel" in tags(actor)]
proxies = [actor for actor in scope if "LB.PR010.CollisionProxy" in tags(actor)]
service_banks = [actor for actor in scope if "LB.PR010.ServiceDeck.InstalledRouting" in tags(actor)]
access_hatches = [actor for actor in scope if "LB.PR010.ServiceDeck.AccessDetail" in tags(actor)]
plates = [actor for actor in scope if "LB.PR010.StackIdentityPlate" in tags(actor)]
visible_text = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor) and "LB.PR010.StackPositionID.Reverse.v103" in tags(actor)]
stack_camera = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Evidence.StackID" in tags(actor)]
lights = [actor for actor in scope if isinstance(actor, unreal.PointLight) and "LB.PR010.Lighting.Calibrated.v103" in tags(actor)]
candidate_tags = [str(tag) for actor in scope for tag in actor.tags if str(tag).startswith("LB.Asset.Candidate")]
missing_accepted = [actor.get_actor_label() for actor in scope if ACCEPTED_TAG not in tags(actor)]
texts = [str(actor.text_render.get_editor_property("text")) for actor in scope if isinstance(actor, unreal.TextRenderActor)]
failures = []
if len(scope) != 307:
    failures.append(f"expected 307 PR010 actors, found {len(scope)}")
if len(native) != 1:
    failures.append(f"expected one PR010 native authority, found {len(native)}")
else:
    if native[0].get_actor_location().distance(unreal.Vector(1350, -2000, 0)) > 0.01:
        failures.append("PR010 datum mismatch")
    if abs(native[0].get_actor_rotation().yaw + 90.0) > 0.01:
        failures.append("PR010 yaw mismatch")
if len(pr009_native) != 1:
    failures.append(f"accepted PR009 authority count changed: {len(pr009_native)}")
if (len(carriers), len(stacks), len(guards), len(proxies)) != (8, 9, 8, 52):
    failures.append(f"carrier/stack/guard/proxy mismatch: {len(carriers)}/{len(stacks)}/{len(guards)}/{len(proxies)}")
if len(service_banks) != 4 or any(size(actor) != (58.8, 270.0, 106.0) for actor in service_banks):
    failures.append(f"service-bank contract mismatch: {len(service_banks)} {[size(actor) for actor in service_banks]}")
if len(access_hatches) != 4 or any(size(actor) != (13.05, 270.0, 65.0) for actor in access_hatches):
    failures.append(f"access-hatch contract mismatch: {len(access_hatches)} {[size(actor) for actor in access_hatches]}")
if len(plates) != 9 or any(size(actor) != (90.0, 8.0, 32.0) for actor in plates):
    failures.append(f"stack-plate contract mismatch: {len(plates)} {[size(actor) for actor in plates]}")
if len(visible_text) != 9 or any(not actor.text_render.get_editor_property("visible") for actor in visible_text):
    failures.append(f"visible stack-ID contract mismatch: {len(visible_text)}")
if len(stack_camera) != 1:
    failures.append(f"stack-ID fixed camera count mismatch: {len(stack_camera)}")
actual_lights = sorted(round(actor.point_light_component.get_editor_property("intensity"), 3) for actor in lights)
if actual_lights != [65.0, 95.0, 95.0, 105.0]:
    failures.append(f"calibrated light contract mismatch: {actual_lights}")
if candidate_tags:
    failures.append(f"{len(candidate_tags)} candidate tags remain in accepted PR010 scope")
if missing_accepted:
    failures.append(f"{len(missing_accepted)} PR010 actors lack accepted tag")
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in texts):
    failures.append("working-title branding found in accepted PR010 scope")
required_assets = [
    "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103/SM_CA_MW_PR010_InstalledServiceBank_v103",
    "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103/SM_CA_MW_PR010_ServiceAccessHatchSection_v103",
    "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103/SM_CA_MW_PR010_StackIdentityPlate_v103",
    "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103/Materials/M_CA_MW_PR010_StackLabel_v103",
]
missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]
if missing_assets:
    failures.append(f"missing referenced release assets: {missing_assets}")

report = {
    "$schema": "cairnwell/audit/pr010-accepted-static-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "status": "PASS__PR010_V103_ACCEPTED_EXACT_MAP_AUTHORITY_GEOMETRY_IDENTITY_BRANDING_IMMUTABLE_TAGS__RUNTIME_GATES_REQUIRED" if not failures else "FAIL__PR010_V103_ACCEPTED_STATIC",
    "pr010_scope_actor_count": len(scope),
    "pr010_native_count": len(native),
    "retained_pr009_native_count": len(pr009_native),
    "carrier_count": len(carriers),
    "stack_count": len(stacks),
    "open_guard_count": len(guards),
    "collision_proxy_count": len(proxies),
    "service_bank_count": len(service_banks),
    "access_hatch_count": len(access_hatches),
    "stack_plate_count": len(plates),
    "visible_stack_text_count": len(visible_text),
    "candidate_tag_count": len(candidate_tags),
    "accepted_tag_count": len(scope) - len(missing_accepted),
    "missing_assets": missing_assets,
    "press_train_datums": "TBC_NOT_INVENTED",
    "failures": failures,
  }
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
