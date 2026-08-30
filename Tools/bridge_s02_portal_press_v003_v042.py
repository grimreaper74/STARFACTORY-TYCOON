"""Use the existing shared powered conveyor to close S02's two process gaps."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
CONVEYOR_PATH = "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661"
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_s02_shared_conveyors_v042.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
TAG = unreal.Name("LB.PressShop.2126.v003.S02SharedConveyors.v042")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


for path, expected in EXPECTED.items():
    if digest(path) != expected:
        raise RuntimeError("Protected map changed before S02 conveyor bridge: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
if any(TAG in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("S02 shared-conveyor bridge v042 already applied")
mesh = unreal.load_asset(CONVEYOR_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Existing shared powered conveyor asset unavailable")

# The new S02 portal is 8 m long on X; the feeder and S03 leave two measured
# 6.7 m gaps.  Use the approved 5.2 m support mesh at an honest 1.24 X scale,
# keeping 12 cm mechanical clearance at each end instead of inventing rollers.
bridges = [
    ("2126 v003 | S02 shared infeed powered conveyor", -3442.5),
    ("2126 v003 | S02 shared outfeed powered conveyor", -1973.0),
]
created = []
for label, x in bridges:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, 0.0, 122.0), unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not place shared conveyor")
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(1.24, 1.0, 1.0))
    actor.tags = [TAG, unreal.Name("LB.Process.SharedPoweredConveyor")]
    created.append(actor)

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save S02 shared-conveyor bridge")
for path, expected in EXPECTED.items():
    if digest(path) != expected:
        raise RuntimeError("Protected map changed during S02 conveyor bridge: " + str(path))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__V003_S02_SHARED_CONVEYOR_BRIDGE_V042",
    "candidate_map": MAP,
    "shared_mesh": CONVEYOR_PATH,
    "created": [{"label": actor.get_actor_label(), "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z], "scale": [1.24, 1.0, 1.0]} for actor in created],
    "new_roller_meshes": 0,
    "roof_created": False,
    "protected_hashes": {str(path): digest(path) for path in EXPECTED},
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_S02_SHARED_CONVEYOR_BRIDGE_V042_PASS")
