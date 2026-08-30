"""Localise the reused robot mesh so v002 passes asset-reference restrictions.

The source robot is never modified.  A candidate-owned duplicate is created
once and assigned only to the four candidate instances, preserving their
transforms and candidate-local paint override.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
SOURCE = "/Game/Meshes/Robot/SM_RoboArm04"
DEST = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Meshes/SM_LB_PS2126_RoboArm_v001"
PAINT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials/M_LB_PS2126v002_AutomationSteelReadable"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_robot_localize_v016.json"
TAG = unreal.Name("LB.PressShop.2126.v002.RobotLocalize.v016")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v016 robot localisation already applied")

if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
    raise RuntimeError("Source robot mesh missing")
if not unreal.EditorAssetLibrary.does_asset_exist(DEST):
    duplicate = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
    if duplicate is None:
        raise RuntimeError("Could not duplicate robot mesh into candidate content")
robot_mesh = unreal.load_asset(DEST)
paint = unreal.load_asset(PAINT)
if not isinstance(robot_mesh, unreal.StaticMesh):
    raise RuntimeError("Candidate robot duplicate is not a static mesh")
if not isinstance(paint, unreal.Material):
    raise RuntimeError("Candidate robot paint is missing")

changed = []
for label in (
    "ROBOT v002 | S01 laser-tend robot",
    "ROBOT v002 | S02 draw quality robot",
    "ROBOT v002 | S04 pierce handling robot",
    "ROBOT v002 | S06 vision stack robot",
):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Missing candidate robot actor " + label)
    component = actor.static_mesh_component
    previous_location = actor.get_actor_location()
    previous_rotation = actor.get_actor_rotation()
    previous_scale = actor.get_actor_scale3d()
    component.set_static_mesh(robot_mesh)
    component.set_material(0, paint)
    if actor.get_actor_location() != previous_location or actor.get_actor_rotation() != previous_rotation or actor.get_actor_scale3d() != previous_scale:
        raise RuntimeError("Robot transform changed while localising " + label)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Automation.LocalCandidateMesh")]
    changed.append(label)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v016 robot asset localisation")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROBOT_REFERENCE_LOCALIZED_TO_CANDIDATE_CONTENT",
    "candidate_map": MAP,
    "source_mesh": SOURCE,
    "candidate_mesh": DEST,
    "changed_instances": changed,
    "source_mesh_modified": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_ROBOT_LOCALIZE_V016_PASS")
