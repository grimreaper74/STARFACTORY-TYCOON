"""Integrate accepted PR-004 v009 art into a preserved Press Shop v003 candidate."""

import json
import re
from pathlib import Path

import unreal


SOURCE_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v003"
ANCHOR = unreal.Vector(-5050.0, -2000.0, 0.0)
ROOT = Path(unreal.Paths.project_dir())
OUTPUT = ROOT / "Saved/Audits/press_shop_pr004_v009_integration_v003.json"
PREFIX = "LB_INT_PR004_V009_"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def excluded_source(label):
    return any(token in label for token in (
        "LB_PR004_Envelope_",
        "LB_PR004_HeightDatum_",
        "LB_PR004_LockedFloor_",
        "LB_PR004_VENDOR_",
    ))


def clean_label(label):
    label = label.removeprefix("LB_PR004_")
    return re.sub(r"[^A-Za-z0-9_]+", "_", label)


levels.load_level(SOURCE_MAP)
source_rows = []
excluded = []
for actor in actors.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    if excluded_source(label):
        excluded.append(label)
        continue
    component = actor.get_editor_property("static_mesh_component")
    mesh = component.get_editor_property("static_mesh")
    if mesh is None:
        continue
    transform = actor.get_actor_transform()
    source_rows.append({
        "label": label,
        "mesh": mesh.get_path_name(),
        "location": list(transform.translation.to_tuple()),
        "rotation": list(transform.rotation.rotator().to_tuple()),
        "scale": list(transform.scale3d.to_tuple()),
        "mobility": str(component.get_editor_property("mobility")),
    })

if not source_rows:
    raise RuntimeError("No PR-004 source mesh actors found")

# The derivative is prepared in a separate editor session to avoid Unreal
# retaining the duplicated UWorld as a standalone package during a map switch.
if not unreal.EditorAssetLibrary.does_asset_exist(DEST_MAP):
    raise RuntimeError("Run prepare_press_shop_integration_candidate_v003.py first")
levels.load_level(DEST_MAP)

removed = []
for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.startswith(PREFIX) or (
        label.startswith("LB_INT_FRONT_") and "PR004" in label
    ):
        removed.append(label)
        actors.destroy_actor(actor)

created = []
for row in source_rows:
    mesh = unreal.load_asset(row["mesh"])
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing source mesh {row['mesh']}")
    local = row["location"]
    location = unreal.Vector(ANCHOR.x + local[0], ANCHOR.y + local[1], ANCHOR.z + local[2])
    rotation = unreal.Rotator(*row["rotation"])
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(PREFIX + clean_label(row["label"]))
    actor.set_actor_scale3d(unreal.Vector(*row["scale"]))
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_editor_property(
        "mobility",
        unreal.ComponentMobility.MOVABLE if "MOVABLE" in row["mobility"].upper() else unreal.ComponentMobility.STATIC,
    )
    actor.set_editor_property("tags", [
        unreal.Name("LB.Station.PR-004"),
        unreal.Name("LB.Asset.Candidate.v009"),
        unreal.Name("LB.Integration.PressShop.v003"),
        unreal.Name("LB.Visual.UserAccepted"),
    ])
    created.append(actor.get_actor_label())

datum = actors.spawn_actor_from_class(unreal.TargetPoint, ANCHOR, unreal.Rotator())
datum.set_actor_label(PREFIX + "Datum")
datum.set_editor_property("tags", [unreal.Name("LB.Station.PR-004"), unreal.Name("LB.Station.Datum")])

# Fixed evidence cameras: normal management framing plus a close cell review.
camera_specs = (
    ("CAM_FrontEndDirty", unreal.Vector(-7800.0, 2200.0, 3150.0), unreal.Vector(-5450.0, -1750.0, 100.0), 49.0),
    ("CAM_PR004CloseDirty", unreal.Vector(-5850.0, -330.0, 720.0), unreal.Vector(-5050.0, -2000.0, 120.0), 44.0),
)
for suffix, location, target, fov in camera_specs:
    camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
    camera.set_actor_label(PREFIX + suffix)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    camera.get_editor_property("camera_component").set_editor_property("field_of_view", fov)

if not levels.save_current_level():
    raise RuntimeError("Failed saving Press Shop v003 integration candidate")

result = {
    "status": "INTEGRATION_CANDIDATE__VISUAL_REVIEW_REQUIRED",
    "source_map": SOURCE_MAP,
    "base_map_preserved": BASE_MAP,
    "destination_map": DEST_MAP,
    "anchor_world_cm": list(ANCHOR.to_tuple()),
    "created_static_mesh_actor_count": len(created),
    "removed_old_pr004_actor_count": len(removed),
    "excluded_validation_actor_count": len(excluded),
    "created_labels": created,
    "removed_labels": removed,
    "excluded_labels": excluded,
    "continuous_floor_policy": "Validation floor excluded; full-map floor and mothballed dressing remain authoritative.",
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_INTEGRATION_V003_PASS actors={len(created)} map={DEST_MAP}")
