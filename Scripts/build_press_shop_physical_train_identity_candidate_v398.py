"""Fresh direct-v386 child mounting four physical train identity meshes.

Only the west/entry identity is fitted for the first visual gate.  The signs are
visual-only, navigation-neutral reusable instances; runtime production authority
and the protected v386 base remain unchanged.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386.umap"
BASE_SHA = "057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PhysicalTrainIdentityCandidate_v398"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PhysicalTrainIdentityCandidate_v398.umap"
DEST = "/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v397"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_physical_train_identity_build_v398.json"
ROWS = {"A": -4300.0, "B": -2100.0, "C": 100.0, "D": 2300.0}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("protected v386 base drift")
if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v398")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v386 child failed")

added = []
for train, y_value in ROWS.items():
    asset_path = f"{DEST}/SM_CA_MW_PressTrainIdentity_{train}_v396"
    mesh = lib.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing physical sign {asset_path}")
    label = f"LB_V398_PRESS_TRAIN_{train}_PHYSICAL_IDENTITY_WEST"
    # TBC visual mount, aligned against the west face of the installed S01 cell.
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(1115.0, y_value, 850.0), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"could not spawn {label}")
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
    component = actor.static_mesh_component
    component.set_collision_profile_name("NoCollision")
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("generate_overlap_events", False)
    component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = [unreal.Name(tag) for tag in (
        f"LB.PressTrain.Identity.Train{train}",
        f"LB.PressTrain.DisplayDesignation.{train}",
        "LB.PressTrain.Identity.AllocatedAutomatically",
        "LB.PressTrain.Stations.S01-S07",
        "LB.FactoryBuilder.ReusableModule",
        "LB.Identity.PhysicalMesh",
        "LB.Identity.VisualOnly.NoRuntimeAuthority",
        "LB.Collision.NoCollision.VisualOnly",
        "LB.Navigation.None",
        "LB.Asset.Candidate.v398",
        "LB.Asset.CandidateNotPromoted",
    )]
    origin, extent = actor.get_actor_bounds(False)
    size = [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0]
    added.append({
        "label": label, "train": train, "asset": asset_path,
        "location_cm": [1115.0, y_value, 850.0],
        "world_size_cm": size,
        "mount_status": "TBC_VISUAL_ALIGNMENT__NOT_ENGINEERING_AUTHORITY",
    })

train_counts = {
    key: sum(1 for actor in actors.get_all_level_actors()
             if f"LB.PressTrain.Installed.TRAIN_{key}" in {str(tag) for tag in actor.tags})
    for key in "ABCD"
}
failures = []
if len(added) != 4:
    failures.append(f"expected four signs, added {len(added)}")
for row in added:
    sx, sy, sz = row["world_size_cm"]
    if not (14.0 <= sx <= 17.0 and 255.0 <= sy <= 265.0 and 74.0 <= sz <= 78.0):
        failures.append(f"world sign bounds unexpected {row['label']}: {row['world_size_cm']}")
if train_counts != {"A": 338, "B": 338, "C": 338, "D": 338}:
    failures.append(f"train actor contract changed: {train_counts}")
if not levels.save_current_level():
    failures.append("could not save v398")
if sha(BASE_FILE) != BASE_SHA:
    failures.append("protected v386 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-physical-train-identity-build-v398/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_DIRECT_V386_PHYSICAL_IDENTITY_CANDIDATE__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V398_NOT_A_PARENT",
    "base": BASE, "base_sha256": BASE_SHA,
    "map": MAP, "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "added_physical_identity": added, "train_actor_counts": train_counts,
    "factory_builder_contract": {
        "reusable_mesh_family": True,
        "automatic_designations": ["A", "B", "C", "D"],
        "stable_save_guid_required": True,
        "future_player_custom_display_name": True,
        "runtime_allocator_implementation": "OPEN_NOT_CLAIMED",
    },
    "unchanged_contracts": ["v386 materials", "v386 lighting", "train geometry", "train transforms", "collision", "navigation", "runtime authority", "production state", "save authority"],
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
