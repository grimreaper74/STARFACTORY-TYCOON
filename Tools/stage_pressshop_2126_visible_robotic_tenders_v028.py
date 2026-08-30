"""Move existing reused robot tenders to legible operator-side service poses.

This is a composition pass only: no robot mesh is created, modified or scaled.
Each robot keeps its genuine asset/material and sits outside the press strip,
where it can read as a 2126 autonomous tender in the hero camera.
"""

import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_visible_robotic_tenders_v028.json"
TAG = unreal.Name("LB.PressShop.2126.VisibleTenders.v028")
POSES = {
    "ROBOT | S01 | laser tend robot": (-7900.0, 2450.0, 0.0),
    "ROBOT | S02 | draw quality robot": (-4200.0, -2050.0, 0.0),
    "ROBOT | S04 | pierce handling robot": (-200.0, -2150.0, 0.0),
    "ROBOT | S06 | vision stack robot": (4450.0, -2100.0, 0.0),
}


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
    raise RuntimeError("Visible-tender pass v028 already applied")
rows = []
for label, location in POSES.items():
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected reused robot missing: " + label)
    mesh = actor.static_mesh_component.get_editor_property("static_mesh")
    if mesh is None:
        raise RuntimeError("Expected reused robot mesh missing: " + label)
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_hidden_in_game(False)
    actor.set_is_temporarily_hidden_in_editor(False)
    actor.static_mesh_component.set_visibility(True, True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.PressShop.Automation.Visible")]
    rows.append({"label": label, "asset": mesh.get_path_name(), "location_cm": list(location), "scale_changed": False})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__EXISTING_ROBOTIC_TENDERS_REPOSITIONED_FOR_VISIBLE_2126_AUTOMATION",
    "robots": rows,
    "new_machine_geometry": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_VISIBLE_ROBOTIC_TENDERS_V028_PASS")
