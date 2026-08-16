"""Exact-map static, branding and authority gate for isolated Train A v023."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAReleaseDetailCandidate_v023"
RELEASE_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/ReleaseDetail_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_release_detail_static_v023.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())


def tags(actor):
    return {str(tag) for tag in actor.tags}


scope = [actor for actor in actors if "LB.PressTrain.TrainA.Isolated" in tags(actor)]
presentation = [actor for actor in scope if isinstance(actor, unreal.StaticMeshActor) and "LB.Validation.Environment" not in tags(actor)]
stages = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Stage.S") for tag in tags(actor))]
movers = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Mover.") for tag in tags(actor))]
tooling = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Tooling.") for tag in tags(actor))]
installed = [actor for actor in presentation if "LB.PressTrain.Fixed.InstalledService" in tags(actor)]
release_fixed = [actor for actor in presentation if "LB.PressTrain.Fixed.ReleaseDetail" in tags(actor)]
release_carts = [actor for actor in movers if "LB.PressTrain.ReleaseDetail.DieCart" in tags(actor)]
release_docks = [actor for actor in installed if "LB.PressTrain.ReleaseDetail.DieChangeDock" in tags(actor)]
tooling_loads = [actor for actor in release_fixed if any(tag.endswith("DieCartToolingLoad") for tag in tags(actor))]
frame_detail = [actor for actor in release_fixed if any(tag.endswith("FrameSeamsFasteners") for tag in tags(actor))]
utilities = [actor for actor in release_fixed if any(tag.endswith("SupportedUtilities") for tag in tags(actor))]
states = [actor for actor in release_fixed if any(".ServiceState." in tag for tag in tags(actor))]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in tags(actor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
release_texts = [actor for actor in texts if "LB.PressTrain.ReleaseDetail.Text" in tags(actor)]

minimum = unreal.Vector(1e12, 1e12, 1e12)
maximum = unreal.Vector(-1e12, -1e12, -1e12)
for actor in presentation:
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x)
    minimum.y = min(minimum.y, origin.y - extent.y)
    minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x)
    maximum.y = max(maximum.y, origin.y + extent.y)
    maximum.z = max(maximum.z, origin.z + extent.z)
bounds = [round((maximum.x - minimum.x) * 10, 3), round((maximum.y - minimum.y) * 10, 3), round((maximum.z - minimum.z) * 10, 3)]

expected = {
    "presentation": (len(presentation), 96), "stages": (len(stages), 7),
    "movers": (len(movers), 22), "tooling": (len(tooling), 5),
    "installed": (len(installed), 21), "release_fixed": (len(release_fixed), 22),
    "release_carts": (len(release_carts), 5), "release_docks": (len(release_docks), 5),
    "tooling_loads": (len(tooling_loads), 5), "frame_detail": (len(frame_detail), 5),
    "utilities": (len(utilities), 5), "states": (len(states), 7),
    "cameras": (len(cameras), 4), "texts": (len(texts), 20),
    "release_texts": (len(release_texts), 12),
}
failures = []
for name, (actual, wanted) in expected.items():
    if actual != wanted:
        failures.append(f"expected {wanted} {name}, found {actual}")
if len(scope) != 145:
    failures.append(f"expected 145 scoped actors, found {len(scope)}")
if any(value > limit + 5 for value, limit in zip(bounds, (15000, 56000, 11500))):
    failures.append(f"aggregate visual bounds exceed shared train envelope: {bounds}")
if sum("LB.Asset.Candidate.v023" in tags(actor) for actor in scope) != len(scope):
    failures.append("v023 candidate tag missing from scoped actors")
if sum("LB.Authority.WorldPlacement.TBCNotInvented" in tags(actor) for actor in scope) != len(scope):
    failures.append("TBC world-placement authority tag missing from scoped actors")
text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_values):
    failures.append("working-title branding found in visible Train A text")
if not any("CAIRNWELL AUTOMOTIVE" in value.upper() and "MOORCROSS WORKS" in value.upper() for value in text_values):
    failures.append("Cairnwell Automotive / Moorcross Works identity missing")
required_assets = [f"{RELEASE_ROOT}/{name}" for name in (
    "SM_CA_MW_PT_DieCartRelease_v001", "SM_CA_MW_PT_DieCartToolingLoad_v001",
    "SM_CA_MW_PT_DieChangeDockRelease_v001", "SM_CA_MW_PT_FrameSeamFastenerPack_v001",
    "SM_CA_MW_PT_HoseCableDress_v001", "SM_CA_MW_PT_ServiceStateRunning_v001",
    "SM_CA_MW_PT_ServiceStateStandby_v001", "SM_CA_MW_PT_ServiceStateMaintenance_v001")]
missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]
if missing_assets:
    failures.append(f"missing imported assets: {missing_assets}")
report = {
    "$schema": "cairnwell/audit/press-train-a-release-detail-static-v023/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V023_EXACT_MAP_RELEASE_CARTS_DOCKS_FRAME_DETAIL_SUPPORTED_UTILITIES_DISTINCT_STATES_BRANDING_ENVELOPE_AND_TBC_AUTHORITY__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V023_RELEASE_DETAIL_STATIC__NOT_PROMOTED"),
    "map": MAP, "counts": {name: actual for name, (actual, _wanted) in expected.items()},
    "scope_actor_count": len(scope), "aggregate_visual_bounds_mm": bounds,
    "world_placement": "TBC_NOT_INVENTED", "missing_assets": missing_assets,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
