"""Create v055 with a validation-only installed Press Shop bay around exact-map v054."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAEndpointMaterialStateCandidate_v054"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAInstalledBayContextCandidate_v055"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_installed_bay_context_v055.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v055 from v054: {TARGET}")

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
materials = {
    "charcoal": library.load_asset("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085"),
    "yellow": library.load_asset("/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025/M_CA_MW_PT_SafetyYellowLayered_v025"),
    "concrete": library.load_asset("/Game/LineBoss/Materials/FrontEnd/MI_LB_Wall_Concrete"),
}
if not isinstance(cube, unreal.StaticMesh) or any(value is None for value in materials.values()):
    raise RuntimeError(f"installed-bay assets missing cube={cube} materials={materials}")


def environment_mesh(label, location, scale, material, role):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator())
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Validation.Environment", "LB.Validation.Environment.InstalledBay.v055",
        f"LB.Validation.Environment.InstalledBay.{role}", "LB.Asset.Candidate.v055",
        "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(scale)
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    return actor


# Repeated columns and roof trusses establish industrial scale without implying
# a global production datum. They sit behind/above the isolated train envelope.
columns = []
trusses = []
for index, y_cm in enumerate((-500.0, 500.0, 1500.0, 2500.0, 3500.0, 4500.0, 5500.0), start=1):
    columns.append(environment_mesh(
        f"CA_MW_PTA_InstalledBayColumn_{index:02d}", unreal.Vector(850.0, y_cm, 650.0),
        unreal.Vector(0.55, 0.55, 13.0), materials["charcoal"], "Column"))
    trusses.append(environment_mesh(
        f"CA_MW_PTA_InstalledBayTruss_{index:02d}", unreal.Vector(0.0, y_cm, 1215.0),
        unreal.Vector(18.0, 0.30, 0.32), materials["charcoal"], "Truss"))

# Thin local floor paint clarifies operator and die-change aisles. It is visual
# evidence only; collision/navigation contracts are deliberately unchanged.
floor_markings = []
for index, x_cm in enumerate((-925.0, -1125.0, 925.0), start=1):
    floor_markings.append(environment_mesh(
        f"CA_MW_PTA_InstalledBayFloorMark_{index:02d}", unreal.Vector(x_cm, 2450.0, 3.0),
        unreal.Vector(0.065, 59.0, 0.018), materials["yellow"], "FloorMarking"))

# Give the existing back wall a finite concrete response and illuminate it from
# the bay side so the machinery silhouette no longer disappears into black.
wall = next((a for a in actors_api.get_all_level_actors() if a.get_actor_label() == "CA_MW_PTA_InstalledEvidenceBackWall"), None)
if wall is None:
    raise RuntimeError("installed evidence back wall missing")
wall.static_mesh_component.set_material(0, materials["concrete"])

wall_washes = []
for index, y_cm in enumerate((0.0, 1100.0, 2200.0, 3300.0, 4400.0, 5500.0), start=1):
    location = unreal.Vector(560.0, y_cm, 720.0)
    target = unreal.Vector(900.0, y_cm, 620.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(f"CA_MW_PTA_InstalledBayWallWash_{index:02d}")
    light.tags = [unreal.Name(value) for value in (
        "LB.Validation.Environment", "LB.Validation.Environment.InstalledBay.v055",
        "LB.Validation.Environment.InstalledBay.WallWash", "LB.Asset.Candidate.v055",
        "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 165.0)
    component.set_editor_property("source_width", 700.0)
    component.set_editor_property("source_height", 180.0)
    component.set_editor_property("attenuation_radius", 900.0)
    component.set_light_color(unreal.LinearColor(0.43, 0.48, 0.46, 1.0))
    wall_washes.append(light)

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v055" not in tags:
            tags.append("LB.Asset.Candidate.v055")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if (len(columns), len(trusses), len(floor_markings), len(wall_washes), scope_count) != (7, 7, 3, 6, 180):
    failures.append(
        f"installed-bay cardinality mismatch columns={len(columns)} trusses={len(trusses)} "
        f"floor={len(floor_markings)} wall_washes={len(wall_washes)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v055 installed-bay context candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-installed-bay-context-v055/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V055_LOCAL_INSTALLED_BAY_COLUMNS_TRUSSES_FLOOR_MARKINGS_AND_WALL_WASH__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V055_INSTALLED_BAY_CONTEXT__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET,
    "column_count": len(columns), "truss_count": len(trusses),
    "floor_marking_count": len(floor_markings), "wall_wash_count": len(wall_washes),
    "wall_wash_intensity": 165.0, "scope_actor_count": scope_count,
    "validation_environment_only": True, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
