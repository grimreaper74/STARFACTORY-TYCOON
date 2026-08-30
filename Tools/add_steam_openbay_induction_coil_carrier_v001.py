"""Replace the visual-only wheeled coil AGV base in Steam Open Bay v004.

The retained inbound cell deliberately keeps its delivery lorry as background
context, but the loaded coil is a separate actor above a separately placed
AGV chassis/deck.  This candidate-only pass hides only those two bases and
places a native-Unreal guided induction carrier below the existing project
coil.  No new coil or Meshy geometry is added.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8")
TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamOpenBay_v004"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "SquareMeshyPressTrain_v001" / "Maps" / "LB_PressShop_SteamOpenBay_v004.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_openbay_v004_induction_carrier_v001.json"
TAG = unreal.Name("LB.PressShop.InductionCarrier.v001")
OLD_TAG = unreal.Name("LB.PressShop.InductionCarrier.HiddenLegacyBase")
TARGET_LABELS = {
    "LB_INBOUND_V051_AGV_Chassis",
    "LB_INBOUND_V051_AGV_Deck",
}


def fail(message):
    raise RuntimeError("INDUCTION_CARRIER_V001_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def static_mesh(path):
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing static mesh " + path)
    return asset


def material(path):
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.MaterialInterface):
        fail("missing material " + path)
    return asset


def make_actor(label, mesh, location, scale, material_asset):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator()
    )
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [
        TAG,
        unreal.Name("LB.Asset.Candidate"),
        unreal.Name("LB.Environment.VisualOnly"),
        unreal.Name("LB.Future2126.GuidedCarrier"),
    ]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(*scale))
    component.set_material(0, material_asset)
    return actor


world = unreal.EditorLevelLibrary.get_editor_world()
if world.get_path_name() != TARGET + ".LB_PressShop_SteamOpenBay_v004":
    fail("run only with the v004 candidate map open; current=" + world.get_path_name())
if not TARGET_FILE.is_file():
    fail("candidate map file is missing")

existing = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in existing):
    fail("induction carrier is already present; refusing duplicate placement")

legacy = {actor.get_actor_label(): actor for actor in existing if actor.get_actor_label() in TARGET_LABELS}
if set(legacy) != TARGET_LABELS:
    fail("expected exact separable legacy AGV pair, found=" + repr(sorted(legacy)))
coil = next((actor for actor in existing if actor.get_actor_label() == "LB_INBOUND_V051_AGV_LoadedCoil"), None)
if coil is None:
    fail("the separate loaded project coil is missing")

cube = static_mesh("/Engine/BasicShapes/Cube.Cube")
cylinder = static_mesh("/Engine/BasicShapes/Cylinder.Cylinder")
charcoal = material("/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Materials/M_LB_PS_SteamCharcoal_v004")
steel = material("/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Materials/M_LB_PS_SteamSteel_v004")
yellow = material("/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Materials/M_LB_PS_SteamSafetyYellow_v004")

candidate_hash_before = sha256(TARGET_FILE)
for actor in legacy.values():
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [OLD_TAG]
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)

# All dimensions are centimetres.  The thin discs are visible lift pads, not
# wheels: they sit beneath a broad, almost-square carrier deck with two steel
# cradle rails.  The existing project coil remains untouched at (1350,0,185).
placed = []


def add(label, mesh, location, scale, mat):
    actor = make_actor(label, mesh, location, scale, mat)
    placed.append(actor)
    return actor


add("2126 Induction coil carrier - charcoal deck", cube, (1350.0, 0.0, 72.0), (2.55, 1.48, 0.34), charcoal)
add("2126 Induction coil carrier - upper steel deck", cube, (1350.0, 0.0, 113.0), (2.30, 1.25, 0.14), steel)
add("2126 Induction coil carrier - cradle rail A", cube, (1350.0, -98.0, 140.0), (2.05, 0.13, 0.18), steel)
add("2126 Induction coil carrier - cradle rail B", cube, (1350.0, 98.0, 140.0), (2.05, 0.13, 0.18), steel)
add("2126 Induction coil carrier - safety spine", cube, (1350.0, 0.0, 142.0), (1.25, 0.20, 0.14), yellow)

for suffix, x, y in (("front left", 1150.0, -105.0), ("front right", 1150.0, 105.0), ("rear left", 1550.0, -105.0), ("rear right", 1550.0, 105.0)):
    add("2126 Induction coil carrier - lift pad " + suffix, cylinder, (x, y, 32.0), (0.68, 0.68, 0.18), charcoal)
for suffix, x, y in (("front left", 1150.0, -145.0), ("front right", 1150.0, 145.0), ("rear left", 1550.0, -145.0), ("rear right", 1550.0, 145.0)):
    add("2126 Induction coil carrier - yellow locator " + suffix, cube, (x, y, 104.0), (0.10, 0.10, 0.36), yellow)

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save candidate map")
candidate_hash_after = sha256(TARGET_FILE)
current = list(unreal.EditorLevelLibrary.get_all_level_actors())
if len([actor for actor in current if TAG in actor.tags]) != len(placed):
    fail("placed actor count does not match tag count")
if not all(actor.get_editor_property("bHidden") for actor in legacy.values()):
    fail("legacy AGV chassis/deck were not hidden in the candidate")
if coil.get_editor_property("bHidden"):
    fail("existing project coil was unexpectedly hidden")

payload = {
    "status": "PASS__NATIVE_UNREAL_INDUCTION_COIL_CARRIER_V001",
    "candidate_map": TARGET,
    "candidate_hash_before": candidate_hash_before,
    "candidate_hash_after": candidate_hash_after,
    "legacy_wheel_base_hidden_in_candidate_only": sorted(TARGET_LABELS),
    "retained_separate_project_coil": coil.get_actor_label(),
    "new_native_unreal_actor_count": len(placed),
    "new_actor_labels": [actor.get_actor_label() for actor in placed],
    "design": "Low guided induction carrier with four lift pads and two coil cradle rails; no conventional wheel geometry.",
    "meshy_policy": "No Meshy API request, asset, geometry or coil was used.",
    "honest_status": "Candidate visual look-dev only. The lift pads are a non-gameplay future-industrial visual treatment, not a physical hover simulation claim.",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("INDUCTION_CARRIER_V001=" + json.dumps({"actors": len(placed), "map": TARGET}, sort_keys=True))
