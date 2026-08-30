"""Replace placeholder coil carrier pads in the 2126 candidate with real assets.

Candidate-map only. The working bare coil stays a separate project actor and
is seated on the coil-free Meshy feeder's retained mandrel. The wrapped spare
coil stays a separate project actor and is staged on an existing coil saddle.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_infeed_coilcell_v011.json"
TAG = unreal.Name("LB.PressShop.2126.InfeedCoilCell.v011")
FEEDER = "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001/SM_LB_PS_InfeedCoilFeeder_NoCoil_v001"
SADDLE = "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002"

BARE_LABEL = "S00 | approved bare master coil"
WRAPPED_LABEL = "S00 | approved wrapped master coil"
PLACEHOLDERS = (
    "S00 | carrier warm-white lift pad 0",
    "S00 | carrier warm-white lift pad 1",
    "S00 | guided induction carrier 0",
    "S00 | guided induction carrier 1",
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def actor_by_label(actors, label):
    matches = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one '%s', found %d" % (label, len(matches)))
    return matches[0]


def visible(actor):
    components = actor.get_components_by_class(unreal.PrimitiveComponent)
    return bool(components) and all(component.is_visible() for component in components)


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("infeed coil cell v011 already installed")

bare = actor_by_label(actors, BARE_LABEL)
wrapped = actor_by_label(actors, WRAPPED_LABEL)
for label in PLACEHOLDERS:
    placeholder = actor_by_label(actors, label)
    hide(placeholder)
    placeholder.tags = list(placeholder.tags) + [TAG]

feeder_mesh = unreal.load_asset(FEEDER)
saddle_mesh = unreal.load_asset(SADDLE)
if not isinstance(feeder_mesh, unreal.StaticMesh) or not isinstance(saddle_mesh, unreal.StaticMesh):
    raise RuntimeError("Required native infeed assets were not available")

# The original Meshy coil was centred locally at (-708.8, 95.6, 254.2) cm.
# At 0.85 scale, this aligns the bare project coil with the retained mandrel;
# it also makes the new holder suit the project's 1.9 m coil diameter.
feeder = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-12597.52, -81.26, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
if feeder is None:
    raise RuntimeError("Could not spawn native StaticMeshActor for coil feeder")
feeder.static_mesh_component.set_static_mesh(feeder_mesh)
feeder.set_actor_label("S00 | Meshy coil-free autonomous feeder | native PBR")
feeder.set_actor_scale3d(unreal.Vector(0.85, 0.85, 0.85))
feeder.tags = list(feeder.tags) + [TAG]

# Only these two pre-existing coil actors appear in the map. The bare coil is
# operational on the feeder; the wrapped coil is staged close by for changeover.
bare.set_actor_location(unreal.Vector(-13200.0, 0.0, 216.07), False, False)
wrapped.set_actor_location(unreal.Vector(-15800.0, 1700.0, 160.0), False, False)
bare.tags = list(bare.tags) + [TAG]
wrapped.tags = list(wrapped.tags) + [TAG]
saddle = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-15800.0, 1700.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
if saddle is None:
    raise RuntimeError("Could not spawn native StaticMeshActor for changeover saddle")
saddle.static_mesh_component.set_static_mesh(saddle_mesh)
saddle.set_actor_label("S00 | wrapped coil changeover saddle | reused kit asset")
saddle.tags = list(saddle.tags) + [TAG]

# Fail closed on separate inventory: no embedded Meshy coil actor is allowed,
# and both protected project coil actors must remain visible and unique.
after = list(unreal.EditorLevelLibrary.get_all_level_actors())
for label in (BARE_LABEL, WRAPPED_LABEL):
    item = actor_by_label(after, label)
    if not visible(item):
        raise RuntimeError("Required separate coil became hidden: " + label)
if len([actor for actor in after if "master coil" in actor.get_actor_label().lower()]) != 2:
    raise RuntimeError("coil inventory is not exactly the two approved project coils")
if any("carrier warm-white" in actor.get_actor_label().lower() and visible(actor) for actor in after):
    raise RuntimeError("placeholder lift pad still visible")
if any("guided induction carrier" in actor.get_actor_label().lower() and visible(actor) for actor in after):
    raise RuntimeError("placeholder induction carrier still visible")

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed during candidate-only infeed installation")

receipt = {
    "status": "PASS__REAL_MESHY_INFEED_AND_EXISTING_COIL_SADDLE_REPLACE_PLACEHOLDER_PADS",
    "candidate_map": MAP,
    "hidden_placeholders": list(PLACEHOLDERS),
    "new_candidate_actor": {"label": feeder.get_actor_label(), "mesh": feeder_mesh.get_path_name(), "scale": 0.85},
    "reused_candidate_actor": {"label": saddle.get_actor_label(), "mesh": saddle_mesh.get_path_name()},
    "coils": {
        "exactly_two_project_coils": [BARE_LABEL, WRAPPED_LABEL],
        "bare_mode": "separate project coil positioned on the feeder mandrel",
        "wrapped_mode": "separate project coil positioned on the existing changeover saddle",
        "embedded_meshy_coils": 0,
    },
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_INFEED_COILCELL_V011_PASS=" + json.dumps(receipt, sort_keys=True))
