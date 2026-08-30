"""Hide superseded primitive press blockouts behind the compact Meshy line.

The original candidate was useful as a spatial sketch, but its native cube
presses were left visible after the real Meshy replacements were installed.
They overlap the genuine assets and are the direct cause of the screenshot
drift.  This pass hides, rather than deletes, only those tagged-by-name
candidate placeholders.  Coils, carriers, real Meshy presses, real conveyors
and protected source maps are not modified.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_blockout_overlay_removal_v007.json"
TAG = unreal.Name("LB.PressShop.2126.BlockoutOverlayRemoval.v007")

PREFIXES = (
    "S01 | laser ",
    "S01 | flat stock bridge",
    "S01 | adaptive laser blanking |",
    "S02 Draw Nexus |",
    "S03 Trim Array |",
    "S04 Pierce Cell |",
    "S02 | Draw |",
    "S03 | Trim |",
    "S04 | Pierce |",
    "S05 | Edge |",
    "S02-S05 | overhead transfer spine",
    "transfer | crossbar bridge",
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("Blockout-overlay removal v007 already exists")

hidden = []
for actor in actors:
    label = actor.get_actor_label()
    if not label.startswith(PREFIXES):
        continue
    hide(actor)
    actor.tags = list(actor.tags) + [TAG]
    hidden.append(label)

if len(hidden) < 30:
    raise RuntimeError("Expected at least 30 superseded blockout parts; found %d" % len(hidden))

must_remain_visible = (
    "MESHY | S02 Draw / form | reused press asset",
    "MESHY | S03 Trim | reused press asset",
    "MESHY | S04 Pierce | reused press asset",
    "MESHY | S05 Flange / hem | reused press asset",
    "MESHY | S06 Vision / outfeed | reused press asset",
    "S00 | approved bare master coil",
    "S00 | approved wrapped master coil",
)
labels = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
missing = [label for label in must_remain_visible if label not in labels]
if missing:
    raise RuntimeError("Required real asset missing: " + ", ".join(missing))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate with blockout overlays hidden")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only blockout removal")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__SUPERSEDED_BLOCKOUTS_HIDDEN_REAL_MESHY_AND_PROJECT_COILS_PRESERVED",
    "candidate_map": MAP,
    "hidden_candidate_only_blockout_actors": hidden,
    "required_real_assets_preserved": list(must_remain_visible),
    "new_meshy_generation_or_edit": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_BLOCKOUT_OVERLAY_REMOVAL_V007_PASS: %d hidden" % len(hidden))
