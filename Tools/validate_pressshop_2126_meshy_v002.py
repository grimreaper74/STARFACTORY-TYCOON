"""Read-only verification for the compact 2126 Meshy press candidate."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
V438 = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED_V438 = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_meshy_validation_v002.json"
PRESSES = {
    "MESHY | S02 Draw / form | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S02_DrawForm_MeshyClean_v001",
    "MESHY | S03 Trim | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "MESHY | S04 Pierce | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "MESHY | S05 Flange / hem | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "MESHY | S06 Vision / outfeed | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
}
OLD_PREFIXES = ("S02 Draw Nexus |", "S03 Trim Array |", "S04 Pierce Cell |", "S05 Edge Forge |", "S06 | vision")


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_MESHY_VALIDATION_V002_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def dimensions(mesh):
    box = mesh.get_bounding_box()
    return [round(box.max.x - box.min.x, 2), round(box.max.y - box.min.y, 2), round(box.max.z - box.min.z, 2)]


if not V438.is_file() or sha256(V438) != EXPECTED_V438:
    fail("protected v438 evidence map hash is not the recorded immutable value")
if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("candidate map missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
visible_presses = []
for label, expected_path in PRESSES.items():
    actor = by_label.get(label)
    if actor is None or not isinstance(actor, unreal.StaticMeshActor):
        fail("missing reused Meshy press " + label)
    mesh = actor.static_mesh_component.static_mesh
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name().split(".")[0] != expected_path:
        fail("wrong mesh bound to " + label)
    if not actor.static_mesh_component.is_visible():
        fail("reused Meshy press is hidden: " + label)
    location = actor.get_actor_location()
    visible_presses.append({
        "label": label,
        "asset": mesh.get_path_name(),
        "location_cm": [round(location.x, 1), round(location.y, 1), round(location.z, 1)],
        "yaw": round(actor.get_actor_rotation().yaw, 1),
        "bounds_cm": dimensions(mesh),
        "triangles_lod0": int(mesh.get_num_triangles(0)),
    })

hidden_first_pass = []
for actor in actors:
    if actor.get_actor_label().startswith(OLD_PREFIXES):
        components = actor.get_components_by_class(unreal.PrimitiveComponent)
        if not components or any(component.is_visible() for component in components):
            fail("first-pass placeholder remains visible: " + actor.get_actor_label())
        hidden_first_pass.append(actor.get_actor_label())
if len(hidden_first_pass) < 40:
    fail("expected a complete hidden record of first-pass blockouts")

project_coils = []
for actor in actors:
    if unreal.Name("LB.Reused.ProjectCoil") in actor.tags:
        project_coils.append(actor.get_actor_label())
if len(project_coils) != 2:
    fail("expected exactly the separate wrapped and bare project coils, found %d" % len(project_coils))

roof_labels = [
    actor.get_actor_label()
    for actor in actors
    if isinstance(actor, unreal.StaticMeshActor)
    and "roof" in actor.get_actor_label().lower()
    and actor.static_mesh_component.is_visible()
]
if roof_labels:
    fail("visible roof-labelled mesh exists in roofless candidate: " + ", ".join(roof_labels))

camera_labels = {actor.get_actor_label() for actor in actors}
for label in ("CAM | 2126 Steam hero overview", "CAM | 2126 operator line", "CAM | 2126 draw nexus"):
    if label not in camera_labels:
        fail("missing review camera " + label)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CANDIDATE_HAS_FIVE_VISIBLE_REUSED_MESHY_PRESSES_AND_NO_VISIBLE_BLOCKOUTS",
    "candidate_map": MAP,
    "candidate_actor_count": len(actors),
    "presses": visible_presses,
    "hidden_first_pass_blockout_count": len(hidden_first_pass),
    "separate_project_coils": project_coils,
    "roofless_visible_mesh_check": "PASS",
    "review_cameras": ["CAM | 2126 Steam hero overview", "CAM | 2126 operator line", "CAM | 2126 draw nexus"],
    "protected_v438_sha256": sha256(V438),
    "honest_status": "structural and asset validation only; visual screenshot review remains required",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MESHY_VALIDATION_V002_PASS: presses=%d hidden_blockouts=%d" % (len(visible_presses), len(hidden_first_pass)))
