"""Read-only placement audit for the v438-derived Steam candidate map."""
import hashlib
import json
import re
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
PROTECTED_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "press_shop_steam_candidate_layout_audit_v001.json"
KEYWORDS = re.compile(r"press|train|coil|agv|decoiler|feed|transfer|conveyor|inspect|dunnage|s0[1-7]|buildauthority|bay", re.IGNORECASE)


def fail(message):
    raise RuntimeError("PRESS_SHOP_STEAM_CANDIDATE_AUDIT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def vector_tuple(vector):
    return [round(vector.x, 3), round(vector.y, 3), round(vector.z, 3)]


if not PROTECTED_FILE.is_file():
    fail("protected v438 map source missing")
source_hash_before = sha256(PROTECTED_FILE)
if not unreal.EditorLoadingAndSavingUtils.load_map(CANDIDATE):
    fail("could not load cloned Steam candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
relevant = []
camera_records = []
light_counts = {}
for actor in actors:
    label = actor.get_actor_label()
    class_name = actor.get_class().get_name()
    if "Light" in class_name:
        light_counts[class_name] = light_counts.get(class_name, 0) + 1
    if isinstance(actor, unreal.CameraActor):
        camera_records.append({"label": label, "location_cm": vector_tuple(actor.get_actor_location()), "rotation": str(actor.get_actor_rotation())})
    searchable = " ".join((label, class_name, str(actor.tags)))
    if not KEYWORDS.search(searchable):
        continue
    meshes = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        # UE 5.8 exposes the mesh reference as an editor property rather than
        # the older get_static_mesh() Python wrapper method.
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None:
            meshes.append(mesh.get_path_name())
    origin, extent = actor.get_actor_bounds(False)
    relevant.append({
        "label": label,
        "class": class_name,
        "location_cm": vector_tuple(actor.get_actor_location()),
        "bounds_origin_cm": vector_tuple(origin),
        "bounds_extent_cm": vector_tuple(extent),
        "tags": [str(tag) for tag in actor.tags],
        "static_meshes": meshes,
    })

source_hash_after = sha256(PROTECTED_FILE)
if source_hash_before != source_hash_after:
    fail("protected v438 source changed during read-only candidate audit")

report = {
    "status": "PASS__READ_ONLY_STEAM_CANDIDATE_LAYOUT_AUDIT",
    "candidate": CANDIDATE,
    "total_actor_count": len(actors),
    "camera_count": len(camera_records),
    "cameras": camera_records,
    "light_counts_by_class": light_counts,
    "relevant_actor_count": len(relevant),
    "relevant_actors": relevant,
    "protected_v438_sha256_before": source_hash_before,
    "protected_v438_sha256_after": source_hash_after,
    "next_gate": "select a documented empty press-bay placement in this clone before spawning any new candidate press actor",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_STEAM_CANDIDATE_LAYOUT_AUDIT=" + json.dumps({"actors": len(actors), "relevant": len(relevant), "cameras": len(camera_records)}, sort_keys=True))
