"""Correct the candidate line from the generic asset axis to the documented v438 bay flow.

The read-only map audit shows receiving -> coil store -> front end -> press
trains -> tooling arranged along world +X.  The isolated source review used
+Y.  This candidate-only correction rotates/repositions the 20 actors already
tagged by v001; it does not create duplicates, touch v438, or change assets.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
PROTECTED_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "square_meshy_press_train_steam_layout_v002.json"
TAG = unreal.Name("LB.PressShop.SquareMeshy.SteamCandidate.v001")

# Each tuple is position in centimetres and UE yaw.  The five presses form a
# continuous left-to-right material line between the map's existing front-end,
# train and tooling bays.  -X remains the operator facade.
TRANSFORMS = {
    "S02 Draw/Form - new square-style candidate": ((1202.0, -4300.0, 0.0), 0.0),
    "S03 Trim - new square-style candidate": ((3216.0, -4300.0, 0.0), 90.0),
    "S04 Pierce - new square-style candidate": ((4930.0, -4300.0, 0.0), 0.0),
    "S05 Flange/Hem - new square-style candidate": ((6583.0, -4300.0, 0.0), 90.0),
    "S06 Vision/Outfeed - new square-style candidate": ((8368.0, -4300.0, 0.0), 90.0),
    "Reused native transfer conveyor frame 01": ((2228.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor belt 01": ((2228.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor frame 02": ((4204.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor belt 02": ((4204.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor frame 03": ((5656.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor belt 03": ((5656.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor frame 04": ((7510.0, -4300.0, 0.0), 270.0),
    "Reused native transfer conveyor belt 04": ((7510.0, -4300.0, 0.0), 270.0),
    "S01 Decoiler base - reused": ((-2800.0, -4300.0, 0.0), 270.0),
    "S01 Decoiler spindle - reused": ((-2800.0, -4300.0, 0.0), 270.0),
    "S01 Straightener feed - reused": ((-1150.0, -4300.0, 0.0), 270.0),
    "S01 Feed bridge - reused": ((-450.0, -4300.0, 0.0), 270.0),
    "S07 Inspection cell - reused": ((9700.0, -4300.0, 0.0), 270.0),
    "Bare project coil - separate": ((-2800.0, -3400.0, 0.0), 0.0),
    "Wrapped project coil - separate": ((-5500.0, -3000.0, 0.0), 0.0),
}


def fail(message):
    raise RuntimeError("SQUARE_MESHY_STEAM_LAYOUT_V002_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not PROTECTED_FILE.is_file():
    fail("protected v438 source map is missing")
source_hash_before = sha256(PROTECTED_FILE)
if not unreal.EditorLoadingAndSavingUtils.load_map(CANDIDATE):
    fail("could not load Steam candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
tagged = [actor for actor in actors if TAG in actor.tags]
if len(tagged) != len(TRANSFORMS):
    fail("expected %d v001 candidate actors, found %d" % (len(TRANSFORMS), len(tagged)))
by_label = {actor.get_actor_label(): actor for actor in tagged}
if set(by_label) != set(TRANSFORMS):
    fail("tagged candidate actor labels are not the exact v001 set")

corrected = []
for label, (location, yaw) in TRANSFORMS.items():
    actor = by_label[label]
    if not actor.set_actor_location(unreal.Vector(*location), False, False):
        fail("could not reposition " + label)
    if not actor.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0), False):
        fail("could not rotate " + label)
    corrected.append({"label": label, "location_cm": list(location), "yaw": yaw})

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save corrected Steam candidate map")
source_hash_after = sha256(PROTECTED_FILE)
if source_hash_before != source_hash_after:
    fail("protected v438 source map changed during candidate correction")

report = {
    "status": "PASS__V438_ZONE_ALIGNED_SQUARE_MESHY_PRESS_LINE",
    "candidate": CANDIDATE,
    "protected_v438_sha256_before": source_hash_before,
    "protected_v438_sha256_after": source_hash_after,
    "map_zone_basis": "LB_ZONE_PRESS_RECEIVING -> COIL_STORE -> FRONT_END -> TRAINS -> TOOLING lies along world +X",
    "orientation": {"map_material_flow": "+X", "operator_facade": "-X", "source_asset_heading_compensation": "v001 +Y review heading rotated -90 degrees into the v438 bay flow"},
    "corrected_actors": corrected,
    "next_gate": "place the retained lorry/dock/crane inlet in LB_ZONE_PRESS_RECEIVING and make its visual hand-off to this documented press line readable",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("SQUARE_MESHY_STEAM_LAYOUT_V002=" + json.dumps({"corrected": len(corrected)}, sort_keys=True))
