"""Replace the mismatched hero press with the verified square S02 portal press.

Only the isolated v003 candidate map is changed. Existing machines remain in
the map as hidden historical candidates; protected maps are hash-guarded.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
MESH_PATH = "/Game/LineBoss/Candidates/PressShop/S02PortalPressMeshyClean_v002/SM_LB_PS_S02_PortalPress_MeshyClean_v002"
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_s02_portal_press_v041.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
TAG = unreal.Name("LB.PressShop.2126.v003.S02PortalReplacement.v041")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def hide_render_candidate(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected static mesh candidate: " + actor.get_actor_label())
    actor.static_mesh_component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Visual.SupersededS02")]


for path, expected in EXPECTED.items():
    if digest(path) != expected:
        raise RuntimeError("Protected map changed before S02 replacement: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("S02 portal replacement v041 already applied")
mesh = unreal.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Verified S02 portal mesh is unavailable")
replace_labels = (
    "2126 v003 | 02 | draw / form",
    "2126 v003 | 02 | coil-free hero draw/form body",
    "2126 v003 | 02 | coil-free hero draw/form rollers",
)
missing = [label for label in replace_labels if label not in actors]
if missing:
    raise RuntimeError("Candidate replacement actor missing: " + ", ".join(missing))
for label in replace_labels:
    hide_render_candidate(actors[label])

portal = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-2708.0, 0.0, 0.0), unreal.Rotator())
if not isinstance(portal, unreal.StaticMeshActor):
    raise RuntimeError("Could not place S02 portal press")
portal.set_actor_label("2126 v003 | 02 | square portal draw/form press")
portal.static_mesh_component.set_static_mesh(mesh)
portal.tags = [TAG, unreal.Name("LB.Process.S02.DrawForm"), unreal.Name("LB.Visual.MeshyPortal")]
extent = mesh.get_bounds().box_extent
if max(abs(extent.x - 400.0), abs(extent.y - 240.0), abs(extent.z - 360.0)) > 0.01:
    raise RuntimeError("Unexpected imported portal press bounds")

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save S02 replacement in v003 candidate")
for path, expected in EXPECTED.items():
    if digest(path) != expected:
        raise RuntimeError("Protected map changed during S02 replacement: " + str(path))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__V003_S02_PORTAL_PRESS_REPLACEMENT_V041",
    "candidate_map": MAP,
    "replaced_hidden_actors": list(replace_labels),
    "new_actor": portal.get_actor_label(),
    "new_mesh": MESH_PATH,
    "placement_cm": [-2708.0, 0.0, 0.0],
    "bounds_extent_cm": [extent.x, extent.y, extent.z],
    "coils_added": 0,
    "roller_beds_added": 0,
    "roof_created": False,
    "protected_hashes": {str(path): digest(path) for path in EXPECTED},
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_S02_PORTAL_PRESS_REPLACEMENT_V041_PASS")
