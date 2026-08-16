"""Phase 2: configure v343 with upright v040 visuals and retained authority/collision."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"
MESH_PATH = "/Game/LineBoss/Candidates/PressTrains/TrainA/ReadableLabels_v328/SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343.umap"
AUDIT = ROOT / "Saved/Audits/PressTrains/press_train_a_release_integration_candidate_v343.json"
TRAIN_TAG = "LB.PressTrain.Installed.TRAIN_A"
TRAIN_PREFIX = "LB_INST_PTA_"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if AUDIT.exists():
    raise RuntimeError("Refusing to overwrite v343 audit")
if not lib.does_asset_exist(TARGET_MAP) or not levels.load_level(TARGET_MAP):
    raise RuntimeError("v343 clone missing or could not load")

train_actors = []
authorities = []
hidden_presentations = []
collision_components_preserved = 0
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    label = actor.get_actor_label()
    if TRAIN_TAG not in tags and not label.upper().startswith(TRAIN_PREFIX):
        continue
    train_actors.append(actor)
    if actor.get_class().get_name() == "LBPressTrainAStation":
        authorities.append(actor)
        continue
    actor.set_actor_hidden_in_game(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        if component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
            collision_components_preserved += 1
        component.set_visibility(False, True)
        component.set_hidden_in_game(True, True)
    hidden_presentations.append(actor)

if len(authorities) != 1 or len(hidden_presentations) != 337:
    raise RuntimeError(f"Unexpected native inventory: authorities={len(authorities)} presentations={len(hidden_presentations)}")

mesh = lib.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("v040 mesh missing")
replacement = actors_api.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0)
)
replacement.static_mesh_component.set_static_mesh(mesh)
replacement.set_actor_label("CA_MW_PTA_v040_RELEASE_VISUAL_SUBSTRATE_v343")
replacement.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
replacement.static_mesh_component.set_collision_profile_name("NoCollision")
replacement.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
replacement.tags = [unreal.Name(value) for value in (
    "LB.PressTrain.TrainA.ReadableLabelsSource.v040",
    "LB.PressTrain.TrainA.ReleaseIntegrationCandidate.v343",
    "LB.NativeAuthority.Preserved",
    "LB.NativeCollision.PreservedHidden",
    "LB.Collision.NoCollision.VisualOnly",
    "LB.Asset.CandidateNotPromoted",
)]
origin, extent = replacement.get_actor_bounds(False)
replacement.add_actor_world_offset(
    unreal.Vector(3850.0 - origin.x, -4300.0 - origin.y, -(origin.z - extent.z)), False, False
)
origin, extent = replacement.get_actor_bounds(False)
size = [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0]
floor_z = origin.z - extent.z
failures = []
if not (5400.0 <= size[0] <= 5750.0):
    failures.append(f"length {size[0]:.2f}")
if not (900.0 <= size[2] <= 980.0):
    failures.append(f"height {size[2]:.2f}")
if abs(floor_z) > 1.0:
    failures.append(f"floor {floor_z:.3f}")
if collision_components_preserved < 120:
    failures.append(f"collision preservation {collision_components_preserved}")
if failures:
    raise RuntimeError("v343 hard gate failed: " + "; ".join(failures))
if not levels.save_current_level():
    raise RuntimeError("Could not save v343")

payload = {
    "$schema": "cairnwell/audit/press-train-a-release-integration-candidate-v343/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__UPRIGHT_V040_VISUAL_SUBSTRATE__NATIVE_AUTHORITY_AND_COLLISION_PRESERVED__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301",
    "target_map": TARGET_MAP,
    "target_map_sha256": sha256(MAP_FILE),
    "native_train_actor_count": len(train_actors),
    "native_authority_count": len(authorities),
    "native_authority_label": authorities[0].get_actor_label(),
    "hidden_native_presentation_actor_count": len(hidden_presentations),
    "native_collision_components_preserved": collision_components_preserved,
    "replacement_actor": replacement.get_actor_label(),
    "replacement_mesh": MESH_PATH,
    "replacement_rotation_degrees": {"pitch": 0.0, "yaw": -90.0, "roll": 0.0},
    "replacement_bounds_origin_cm": list(origin.to_tuple()),
    "replacement_bounds_size_cm": size,
    "replacement_floor_z_cm": floor_z,
    "replacement_collision": "NoCollision",
    "release_holds": [
        "fixed-camera visual review",
        "visible mover module mapping",
        "collision/navigation regression",
        "Train A runtime/interlock/fault/save regression",
        "whole Press Shop management regression",
    ],
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LB_TRAIN_A_V343_CONFIG_PASS size={size} floor={floor_z}")
unreal.SystemLibrary.quit_editor()
