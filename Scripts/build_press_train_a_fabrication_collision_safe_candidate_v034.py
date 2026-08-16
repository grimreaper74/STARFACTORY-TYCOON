"""Build a collision-safe visual successor directly from retained v027.

Fresh v034 reuses only the scale-correct v033 imported mesh assets.  It replaces
NoCollision presentation meshes in place and deliberately retains every old
blocking/query mesh so authored collision bodies, mover sweeps and native
runtime bindings remain exact.
"""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034.umap"
STAGING = ROOT / "Saved/Audits/PressTrains/press_train_a_fabrication_staging_v033.json"
ASSET_ROOT = "/Game/LineBoss/Candidates/PressTrains/TrainA/Fabrication_v033/Meshes"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_fabrication_collision_safe_build_v034.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def contract(actor):
    component = actor.static_mesh_component
    parent = actor.get_attach_parent_actor()
    return {
        "location": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "parent": parent.get_actor_label() if parent else None,
        "collision_enabled": str(component.get_collision_enabled()),
        "collision_profile": str(component.get_collision_profile_name()),
        "affects_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        "mobility": str(component.get_editor_property("mobility")),
        "cast_shadow": bool(component.get_editor_property("cast_shadow")),
    }


receipt = json.loads(STAGING.read_text(encoding="utf-8"))
if receipt.get("status") != "PASS__336_DETERMINISTIC_LOCAL_PIVOT_FBX_FILES__UNREAL_IMPORT_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("v033 staging receipt is not the expected PASS")
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v034 collision-safe candidate")

asset_by_source = {}
for row in receipt["exports"]:
    mesh = library.load_asset(f"{ASSET_ROOT}/{row['asset_name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing validated v033 mesh {row['asset_name']}")
    asset_by_source[row["source_object"]] = mesh
if len(asset_by_source) != 336:
    raise RuntimeError(f"expected 336 v033 meshes, found {len(asset_by_source)}")

base_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors = actors_api.get_all_level_actors()
train_actors = [
    actor for actor in actors
    if isinstance(actor, unreal.StaticMeshActor)
    and "LB.PressTrain.ProcessDirection.PositiveY" in {str(value) for value in actor.tags}
]
if len(train_actors) != 336:
    raise RuntimeError(f"expected 336 train actors, found {len(train_actors)}")

by_source = {}
for source_name in asset_by_source:
    matches = [
        actor for actor in train_actors
        if actor.get_actor_label() == source_name
        or actor.get_actor_label().startswith(source_name + "_UE")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"runtime identity mismatch {source_name}: {[a.get_actor_label() for a in matches]}")
    by_source[source_name] = matches[0]

before = {name: contract(actor) for name, actor in by_source.items()}
replaced = []
retained_collision = []
failures = []
collision_modes = Counter()

for source_name, actor in by_source.items():
    component = actor.static_mesh_component
    mode = component.get_collision_enabled()
    collision_modes[str(mode)] += 1
    if mode != unreal.CollisionEnabled.NO_COLLISION:
        retained_collision.append({
            "source_object": source_name,
            "actor": actor.get_actor_label(),
            "mesh": component.static_mesh.get_path_name(),
            "collision_enabled": str(mode),
            "collision_profile": str(component.get_collision_profile_name()),
        })
        continue

    new_mesh = asset_by_source[source_name]
    old_mesh = component.static_mesh
    old_materials = [component.get_material(index) for index in range(component.get_num_materials())]
    new_slots = len(new_mesh.get_editor_property("static_materials"))
    if len(old_materials) != new_slots:
        failures.append(
            f"material slot mismatch {source_name}: old={len(old_materials)} new={new_slots}"
        )
        continue
    component.set_static_mesh(new_mesh)
    for index, material in enumerate(old_materials):
        if material is not None:
            component.set_material(index, material)
    actor.tags = list(actor.tags) + [
        unreal.Name("LB.PressTrain.FabricationCollisionSafe.v034"),
        unreal.Name("LB.Asset.Candidate.v034"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    replaced.append({
        "source_object": source_name,
        "actor": actor.get_actor_label(),
        "old_mesh": old_mesh.get_path_name(),
        "new_mesh": new_mesh.get_path_name(),
        "material_slot_count": len(old_materials),
    })

after = {name: contract(actor) for name, actor in by_source.items()}
if before != after:
    failures.append("transform/hierarchy/collision/navigation/mobility/shadow contract changed")
if len(replaced) + len(retained_collision) != 336:
    failures.append(
        f"actor disposition mismatch replaced={len(replaced)} retained={len(retained_collision)}"
    )
if not replaced:
    failures.append("no NoCollision presentation actors were upgraded")
if not retained_collision:
    failures.append("no collision-bearing meshes were retained")

station_count = sum(actor.get_class().get_name() == "LBPressTrainAStation" for actor in actors)
if station_count != 1:
    failures.append(f"native station count {station_count}, expected 1")
if not levels.save_current_level():
    failures.append("could not save v034")
base_hash_after = sha256(BASE_FILE)
if base_hash_before != base_hash_after:
    failures.append("protected v027 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-train-a-fabrication-collision-safe-build-v034/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NO_COLLISION_PRESENTATION_UPGRADED__ALL_BLOCKING_AND_QUERY_MESHES_RETAINED__LIVE_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V034_NOT_A_PARENT",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "validated_mesh_asset_source": ASSET_ROOT,
    "train_actor_count": len(train_actors),
    "collision_modes": dict(collision_modes),
    "presentation_replacement_count": len(replaced),
    "collision_mesh_retained_count": len(retained_collision),
    "native_station_count": station_count,
    "contracts_unchanged_except_mesh_and_provenance": before == after,
    "replaced": replaced,
    "retained_collision": retained_collision,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in (
    "status", "map", "map_sha256", "collision_modes",
    "presentation_replacement_count", "collision_mesh_retained_count",
    "native_station_count", "failures"
)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PRESS_TRAIN_A_FABRICATION_COLLISION_SAFE_V034_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
