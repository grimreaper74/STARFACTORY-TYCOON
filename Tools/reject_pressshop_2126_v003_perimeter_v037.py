"""Reject the v035/036 perimeter test after in-engine composition review."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_perimeter_rejected_v037.json"
TAG = unreal.Name("LB.PressShop.2126.v003.PerimeterRejected.v037")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Perimeter rejection v037 already applied")
hidden = []
for index in range(1, 7):
    for label in ("2126 v003 | open-air perimeter panel %02d" % index, "2126 v003 | perimeter green identity blade %02d" % index):
        actor = actors.get(label)
        if not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError("Perimeter test actor missing: " + label)
        actor.static_mesh_component.set_visibility(False, True)
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Visual.RejectedObstructivePerimeter")]
        hidden.append(label)
if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save isolated v003 candidate")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected map changed during v037")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OBSTRUCTIVE_PERIMETER_EXPERIMENT_REJECTED",
    "candidate_map": MAP,
    "reason": "In-engine management-camera review: panels intruded into the top of the composition.",
    "hidden_candidate_only_components": hidden,
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_PERIMETER_REJECTED_V037_PASS")
