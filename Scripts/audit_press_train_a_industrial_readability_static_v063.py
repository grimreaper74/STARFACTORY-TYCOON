"""Standalone exact-map static gate for isolated Train A v063."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v063"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_industrial_readability_static_v063.json"
EXPECTED_COUPLING = (
    "/Game/LineBoss/Candidates/PressTrains/Shared/DockCouplingEvidence_v003/"
    "SM_CA_MW_PT_DockCouplingEngaged_v003.SM_CA_MW_PT_DockCouplingEngaged_v003"
)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
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
exterior = [actor for actor in presentation if "LB.PressTrain.Fixed.ExteriorDetail" in tags(actor)]
enclosed = [actor for actor in presentation if "LB.PressTrain.Fixed.EnclosedFacade" in tags(actor)]
overhead = [actor for actor in scope if "LB.Validation.ReleaseOverheadLighting" in tags(actor)]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in tags(actor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
couplings = [actor for actor in presentation if "LB.PressTrain.Fixed.DockCouplingEvidence" in tags(actor)]
endpoints = [actor for actor in presentation if "LB.PressTrain.Fixed.CrownEndpointPresentation" in tags(actor)]
access = [actor for actor in exterior if "MaintenanceAccess" in actor.get_actor_label()]

minimum = unreal.Vector(1e12, 1e12, 1e12)
maximum = unreal.Vector(-1e12, -1e12, -1e12)
missing_meshes = []
for actor in presentation:
    component = actor.static_mesh_component
    if component.static_mesh is None:
        missing_meshes.append(actor.get_actor_label())
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x)
    minimum.y = min(minimum.y, origin.y - extent.y)
    minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x)
    maximum.y = max(maximum.y, origin.y + extent.y)
    maximum.z = max(maximum.z, origin.z + extent.z)
bounds = [
    round((maximum.x - minimum.x) * 10, 3),
    round((maximum.y - minimum.y) * 10, 3),
    round((maximum.z - minimum.z) * 10, 3),
]

expected = {
    "scope": (len(scope), 187),
    "presentation": (len(presentation), 142),
    "stages": (len(stages), 7),
    "movers": (len(movers), 22),
    "tooling": (len(tooling), 5),
    "installed": (len(installed), 21),
    "release_fixed": (len(release_fixed), 22),
    "exterior": (len(exterior), 16),
    "enclosed": (len(enclosed), 7),
    "overhead": (len(overhead), 4),
    "cameras": (len(cameras), 5),
    "texts": (len(texts), 6),
    "couplings": (len(couplings), 5),
    "endpoints": (len(endpoints), 7),
    "maintenance_access": (len(access), 4),
}
failures = []
for name, (actual, wanted) in expected.items():
    if actual != wanted:
        failures.append(f"expected {wanted} {name}, found {actual}")
if any(value > limit + 5 for value, limit in zip(bounds, (15000, 56000, 11350))):
    failures.append(f"aggregate visual bounds exceed retained exact envelope: {bounds}")
if missing_meshes:
    failures.append(f"static mesh bindings missing: {missing_meshes}")
if sum("LB.Asset.Candidate.v063" in tags(actor) for actor in scope) != len(scope):
    failures.append("v063 candidate tag missing from scoped actors")
if sum("LB.Authority.WorldPlacement.TBCNotInvented" in tags(actor) for actor in scope) != len(scope):
    failures.append("TBC world-placement authority tag missing from scoped actors")

coupling_bindings = []
for actor in couplings:
    mesh = actor.static_mesh_component.static_mesh
    path = mesh.get_path_name() if mesh else None
    coupling_bindings.append({"actor": actor.get_actor_label(), "mesh": path})
    if path != EXPECTED_COUPLING:
        failures.append(f"v003 coupling mismatch: {actor.get_actor_label()} {path}")

access_bindings = []
for actor in access:
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    access_bindings.append({
        "actor": actor.get_actor_label(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
    })
    if abs(location.x - (-130.0)) > 0.1 or abs(rotation.yaw - 180.0) > 0.1:
        failures.append(f"maintenance access transform mismatch: {actor.get_actor_label()}")

endpoint_expected = {
    "CA_MW_PTA_S01_VisibleBlankFeed_v048": -190.0,
    "CA_MW_PTA_S07_VisiblePanelDischarge_v048": -300.0,
}
endpoint_clearance = []
by_label = {actor.get_actor_label(): actor for actor in scope}
for label, expected_x in endpoint_expected.items():
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"endpoint missing: {label}")
        continue
    x_cm = actor.get_actor_location().x
    endpoint_clearance.append({"actor": label, "x_cm": x_cm})
    if abs(x_cm - expected_x) > 0.1:
        failures.append(f"endpoint camera-clearance mismatch: {label} x={x_cm}")

text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_values):
    failures.append("working-title branding found in visible Train A text")
if not any("CAIRNWELL AUTOMOTIVE" in value.upper() and "MOORCROSS WORKS" in value.upper() for value in text_values):
    failures.append("Cairnwell Automotive / Moorcross Works identity missing")

report = {
    "$schema": "cairnwell/audit/press-train-a-industrial-readability-static-v063/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V063_EXACT_MAP_INDUSTRIAL_READABILITY_AND_WARNING_CLEAN_COUPLINGS__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V063_INDUSTRIAL_READABILITY_STATIC_GATE__NOT_PROMOTED",
    "map": MAP,
    "counts": {name: actual for name, (actual, _wanted) in expected.items()},
    "aggregate_visual_bounds_mm": bounds,
    "coupling_bindings": coupling_bindings,
    "maintenance_access": access_bindings,
    "endpoint_camera_clearance": endpoint_clearance,
    "missing_meshes": missing_meshes,
    "world_placement": "TBC_NOT_INVENTED",
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
