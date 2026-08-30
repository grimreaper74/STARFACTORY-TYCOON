"""Remove one nonessential crane endpoint that blocks the outbound automation shot."""

import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_outbound_lens_v024.json"
TAG = unreal.Name("LB.PressShop.2126.OutboundLens.v024")
BLOCKER = "2126 | autonomous overhead rail right endpoint"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Outbound lens v024 already applied")
blocker = actors.get(BLOCKER)
if not isinstance(blocker, unreal.StaticMeshActor):
    raise RuntimeError("Expected crane endpoint missing")
blocker.set_actor_hidden_in_game(True)
blocker.set_is_temporarily_hidden_in_editor(True)
for component in blocker.get_components_by_class(unreal.PrimitiveComponent):
    component.set_visibility(False, True)
blocker.tags = list(blocker.tags) + [TAG, unreal.Name("LB.CameraClarity.Hidden")]
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OUTBOUND_LENS_CLEARED_WITHOUT_CHANGING_REAL_EQUIPMENT",
    "hidden_nonessential_architecture": BLOCKER,
    "machines_changed": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_LENS_V024_PASS")
