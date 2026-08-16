"""Complete the uncovered upper-hall roof-liner grid in a fresh v235 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v235"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_upper_hall_roof_build_v235.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233.umap"
MATERIAL = "/Game/LineBoss/Candidates/PressShop/ShellReadability_v233/Materials/MI_CA_MW_DeepGraphiteRoofLiner_v233"
X_CENTRES = (-10150.0, -8450.0, -6750.0, -5050.0, -3350.0, -1650.0, 50.0,
             1750.0, 3450.0, 5150.0, 6850.0, 8550.0, 10150.0)
Y_CENTRES = (-5125.0, -3375.0, -1625.0, 125.0, 1875.0, 3625.0, 5125.0)
ROOF_Z = 1900.0
ROOF_SCALE = unreal.Vector(17.0, 17.5, 0.12)
ROOF_LOWER_Z = ROOF_Z - 6.0

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
roof_material = library.load_asset(MATERIAL)
if cube is None or roof_material is None:
    raise RuntimeError("missing roof module dependencies")

existing = []
for actor in actors_api.get_all_level_actors():
    if "LB.Module.FactoryRoofLiner" not in {str(tag) for tag in actor.tags}:
        continue
    location = actor.get_actor_location()
    existing.append((round(location.x, 2), round(location.y, 2)))
existing_set = set(existing)

created = []
failures = []
for ix, x_value in enumerate(X_CENTRES, 1):
    for iy, y_value in enumerate(Y_CENTRES, 1):
        key = (round(x_value, 2), round(y_value, 2))
        if key in existing_set:
            continue
        actor = actors_api.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x_value, y_value, ROOF_Z), unreal.Rotator())
        if actor is None:
            failures.append(f"could not create roof panel {ix:02d}_{iy:02d}")
            continue
        label = f"LB_WHOLE_V235_RoofLiner_{ix:02d}_{iy:02d}"
        actor.set_actor_label(label)
        actor.set_actor_scale3d(ROOF_SCALE)
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(cube)
        component.set_material(0, roof_material)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("can_ever_affect_navigation", False)
        actor.tags = [
            unreal.Name("LB.Module.FactoryRoofLiner"), unreal.Name("LB.Streaming.Press.UpperHall"),
            unreal.Name("LB.Environment.RoofGrid.Completed.v235"), unreal.Name("LB.Asset.Candidate.v235"),
            unreal.Name("LB.Asset.CandidateNotPromoted")]
        created.append({"label": label, "location_cm": [x_value, y_value, ROOF_Z]})

crane_bounds = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    tag_text = " ".join(str(tag) for tag in actor.tags)
    if "Crane" not in label and "Crane" not in tag_text and "Overhead" not in label:
        continue
    if isinstance(actor, unreal.CameraActor):
        continue
    origin, extent = actor.get_actor_bounds(False)
    crane_bounds.append({"label": label, "upper_z_cm": origin.z + extent.z})
max_crane_upper_z = max((row["upper_z_cm"] for row in crane_bounds), default=0.0)
crane_clearance_cm = ROOF_LOWER_Z - max_crane_upper_z

if len(existing) != 20:
    failures.append(f"expected twenty inherited roof panels, found {len(existing)}")
if len(created) != 71:
    failures.append(f"expected seventy-one new roof panels, created {len(created)}")
if crane_clearance_cm < 0.0:
    failures.append(f"roof intersects crane-labelled envelope by {-crane_clearance_cm:.2f} cm")
if not levels.save_current_level():
    failures.append("could not save v235")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v233 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v235.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-upper-hall-roof-build-v235/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__UPPER_HALL_ROOF_GRID_COMPLETED_WITH_SEVENTY_ONE_MODULES__FRESH_VISUAL_RUNTIME_AND_CLEARANCE_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "building_envelope_cm": {"x": [-11000.0, 11000.0], "y": [-6000.0, 6000.0]},
    "inherited_roof_panel_count": len(existing),
    "new_roof_panel_count": len(created),
    "total_roof_panel_count": len(existing) + len(created),
    "new_panels": created,
    "roof_lower_z_cm": ROOF_LOWER_Z,
    "maximum_crane_labelled_upper_z_cm": max_crane_upper_z,
    "minimum_crane_to_roof_clearance_cm": crane_clearance_cm,
    "new_panel_collision": "NoCollision",
    "new_panel_navigation_relevance": False,
    "authority_machine_light_existing_geometry_changes": 0,
    "rejected_non_parent": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v234",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
