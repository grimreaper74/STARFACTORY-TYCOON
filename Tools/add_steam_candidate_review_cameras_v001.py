"""Add repeatable review cameras to the isolated Press Shop Steam candidate.

The cameras are presentation aids only.  They sit exclusively in the cloned
candidate map and are tagged for safe, idempotent replacement on later passes.
They deliberately frame the recovered inbound lorry story and the new press
line together, because that is the visual question currently under review.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_candidate_review_cameras_v001.json"
TAG = unreal.Name("LB.PressShop.SteamCandidate.ReviewCamera.v001")

# Positions are in UE centimetres.  The v438 roof starts over the exterior
# apron, so the cameras must sit *inside* the south edge of the building (not
# outside it) and below the roofline.  Their targets remain in the new
# receiving-to-press composition rather than the old v438 roof geometry.
CAMERAS = (
    {
        "label": "LB_CAM_SteamCandidate_LorryToPress_v001",
        "location": (-10300.0, -5350.0, 1750.0),
        "target": (-1000.0, -4300.0, 350.0),
        "fov": 100.0,
    },
    {
        "label": "LB_CAM_SteamCandidate_PressLineHero_v001",
        "location": (-300.0, -5350.0, 1650.0),
        "target": (4900.0, -4300.0, 350.0),
        "fov": 94.0,
    },
    {
        "label": "LB_CAM_SteamCandidate_LorryClose_v001",
        "location": (-10600.0, -5350.0, 1450.0),
        "target": (-6000.0, -4300.0, 300.0),
        "fov": 66.0,
    },
)


def fail(message):
    raise RuntimeError("STEAM_CANDIDATE_CAMERA_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not PROTECTED.is_file():
    fail("protected v438 map is missing")
source_hash_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(CANDIDATE):
    fail("could not load Steam candidate map")

# Replace only our own prior review cameras; no source or unrelated candidates
# are enumerated for deletion.
for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    if TAG in actor.tags:
        unreal.EditorLevelLibrary.destroy_actor(actor)

placed = []
for spec in CAMERAS:
    start = unreal.Vector(*spec["location"])
    target = unreal.Vector(*spec["target"])
    rotation = unreal.MathLibrary.find_look_at_rotation(start, target)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, start, rotation)
    if actor is None:
        fail("could not spawn " + spec["label"])
    actor.set_actor_label(spec["label"])
    actor.tags = [TAG, unreal.Name("LB.Asset.Candidate"), unreal.Name("LB.NotProcessWIP")]
    actor.get_editor_property("camera_component").set_editor_property("field_of_view", spec["fov"])
    placed.append({
        "label": spec["label"], "location_cm": list(spec["location"]),
        "target_cm": list(spec["target"]), "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
        "fov_degrees": spec["fov"],
    })

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save Steam candidate map")
source_hash_after = sha256(PROTECTED)
if source_hash_before != source_hash_after:
    fail("protected v438 source map changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__REVIEW_CAMERAS_ADDED_TO_STEAM_CANDIDATE_ONLY",
    "candidate": CANDIDATE,
    "protected_v438_sha256_before": source_hash_before,
    "protected_v438_sha256_after": source_hash_after,
    "cameras": placed,
    "honest_status": "camera-only presentation aid; not a Steam screenshot or release approval",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("STEAM_CANDIDATE_REVIEW_CAMERAS=" + json.dumps({"placed": len(placed)}, sort_keys=True))
