"""Recreate the proven inbound-cell cutaway in the isolated Steam candidate.

Historical v532/v551 evidence used a cutaway: roof liners and the far (north)
wall liners were hidden while the structural beams, columns, crane and safety
equipment remained.  This avoids a roof-dominant screenshot and lets the
lorry -> crane/C-hook -> AGV -> press flow read as one composition.

Scope is deliberately narrow: only named liner actors in the cloned candidate
map are hidden.  No protected map, mesh, material, gameplay, or source asset
is changed.  Every altered actor is recorded to allow an exact restoration.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_candidate_cutaway_v001.json"
TAG = unreal.Name("LB.PressShop.SteamCandidate.Cutaway.v001")


def fail(message):
    raise RuntimeError("STEAM_CANDIDATE_CUTAWAY_FAIL: " + message)


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

hidden = []
for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    label = actor.get_actor_label()
    # These are render liners only.  Roof beams / purlins / columns deliberately
    # do not match this test and remain in the cutaway.
    if "RoofLiner" not in label and "NorthWallLiner" not in label:
        continue
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    was_visible = component.is_visible()
    component.set_visibility(False, False)
    actor.set_is_temporarily_hidden_in_editor(True)
    if TAG not in actor.tags:
        actor.tags = list(actor.tags) + [TAG]
    hidden.append({"label": label, "was_visible": was_visible})

if len(hidden) < 10:
    fail("cutaway selection unexpectedly small: " + str(len(hidden)))
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save Steam candidate map")
source_hash_after = sha256(PROTECTED)
if source_hash_before != source_hash_after:
    fail("protected v438 source map changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__PROVEN_INBOUND_CUTAWAY_APPLIED_TO_STEAM_CANDIDATE_ONLY",
    "candidate": CANDIDATE,
    "protected_v438_sha256_before": source_hash_before,
    "protected_v438_sha256_after": source_hash_after,
    "basis": "retained v532/v551 inbound visual decision: remove roof/far wall liners but retain structural beams and columns",
    "hidden_actor_count": len(hidden),
    "hidden_actors": hidden,
    "retained": ["roof beams", "purlins", "columns", "bridge crane", "dock", "lorry", "coil AGV", "new press-line assets"],
    "honest_status": "presentation cutaway only; no runtime, collision, navigation, save, or build authority claim",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("STEAM_CANDIDATE_CUTAWAY=" + json.dumps({"hidden": len(hidden)}, sort_keys=True))
