"""Exact-map static/authority gate for Train A installed-service v017."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAInstalledServiceCandidate_v017"
DETAIL_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/InstalledService_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_installed_service_static_v017.json"
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
mechanical = [actor for actor in presentation if "LB.PressTrain.Fixed.MechanicalBay" in tags(actor)]
stage_detail = [actor for actor in presentation if "LB.PressTrain.Fixed.StageDetail" in tags(actor)]
installed = [actor for actor in presentation if "LB.PressTrain.Fixed.InstalledService" in tags(actor)]
service_banks = [actor for actor in installed if any(tag.endswith("OperatorSide") for tag in tags(actor))]
fixtures = [actor for actor in installed if any(tag.endswith("TaskFixture") for tag in tags(actor))]
die_docks = [actor for actor in installed if any(tag.endswith("DieChangeDock") for tag in tags(actor))]
variants = [actor for actor in installed if any(tag.endswith("TrimScrap") or tag.endswith("PierceSlug") for tag in tags(actor))]
local_lights = [actor for actor in scope if "LB.Validation.LocalTaskLighting" in tags(actor)]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in tags(actor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]

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
    "presentation": (len(presentation), 74), "stages": (len(stages), 7),
    "movers": (len(movers), 22), "tooling": (len(tooling), 5),
    "mechanical": (len(mechanical), 5), "stage_detail": (len(stage_detail), 11),
    "installed": (len(installed), 21), "service_banks": (len(service_banks), 7),
    "fixtures": (len(fixtures), 7), "die_docks": (len(die_docks), 5),
    "variants": (len(variants), 2), "local_lights": (len(local_lights), 7),
    "cameras": (len(cameras), 3), "texts": (len(texts), 8),
}
failures = []
for name, (actual, wanted) in expected.items():
    if actual != wanted:
        failures.append(f"expected {wanted} {name}, found {actual}")
if any(value > limit + 5 for value, limit in zip(bounds, (15000, 56000, 11500))):
    failures.append(f"aggregate visual bounds exceed shared train envelope: {bounds}")
if sum("LB.Asset.Candidate.v017" in tags(actor) for actor in scope) != len(scope):
    failures.append("v017 candidate tag missing from scoped actors")
if sum("LB.Authority.WorldPlacement.TBCNotInvented" in tags(actor) for actor in scope) != len(scope):
    failures.append("TBC world-placement authority tag missing from scoped actors")
text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_values):
    failures.append("working-title branding found in visible Train A text")
if not any("CAIRNWELL AUTOMOTIVE" in value.upper() and "MOORCROSS WORKS" in value.upper() for value in text_values):
    failures.append("Cairnwell Automotive / Moorcross Works identity missing")
required_assets = [f"{DETAIL_ROOT}/{name}" for name in (
    "SM_CA_MW_PT_InstalledServiceBank_v001", "SM_CA_MW_PT_DieChangeDock_v001",
    "SM_CA_MW_PT_S04TrimScrapService_v001", "SM_CA_MW_PT_S05PierceSlugService_v001",
    "SM_CA_MW_PT_LocalTaskFixture_v001")]
missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]
if missing_assets:
    failures.append(f"missing imported assets: {missing_assets}")
report = {
    "$schema": "cairnwell/audit/press-train-a-installed-service-static-v017/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V017_EXACT_MAP_INSTALLED_SERVICE_STAGE_VARIANTS_ENVELOPE_BRANDING_AND_TBC_AUTHORITY__EARLY_DRAW_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V017_STATIC__NOT_PROMOTED",
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
