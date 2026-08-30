"""Read-only current-state audit for the isolated 2126 FullHall candidate."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
SEQUENCE = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sequences/LS_CA_MW_2126_PressShopAutomationLoop_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullhall_current_state_v002.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected authority changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
records = []
class_counts = Counter()
tag_counts = Counter()
mesh_instances = Counter()
mesh_triangles = {}
instance_triangles = 0

for actor in actors:
    label = actor.get_actor_label()
    cls = actor.get_class().get_name()
    class_counts[cls] += 1
    for tag in actor.tags:
        tag_counts[str(tag)] += 1
    if not label.startswith("2126 ") and label != "CAM | 2126 full hall fixed game view":
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    origin, extent = actor.get_actor_bounds(False)
    mesh_path = None
    triangles = 0
    materials = []
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        mesh = component.get_editor_property("static_mesh")
        if isinstance(mesh, unreal.StaticMesh):
            mesh_path = mesh.get_path_name()
            triangles = int(mesh.get_num_triangles(0))
            mesh_instances[mesh_path] += 1
            mesh_triangles[mesh_path] = triangles
            instance_triangles += triangles
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            materials.append(material.get_path_name() if material else None)
    records.append({
        "label": label,
        "class": cls,
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "scale": [scale.x, scale.y, scale.z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "tags": [str(tag) for tag in actor.tags],
        "static_mesh": mesh_path,
        "triangles_lod0": triangles,
        "materials": materials,
        "hidden_in_game": bool(actor.get_editor_property("hidden")),
    })

sequence = unreal.load_asset(SEQUENCE)
if not isinstance(sequence, unreal.LevelSequence):
    raise RuntimeError("native automation Level Sequence missing")
bindings = list(sequence.get_bindings())
sequence_tracks = []
for binding in bindings:
    tracks = list(binding.get_tracks())
    sequence_tracks.append({
        "binding": str(binding.get_display_name()),
        "track_count": len(tracks),
        "track_classes": [track.get_class().get_name() for track in tracks],
        "section_counts": [len(track.get_sections()) for track in tracks],
    })

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("read-only audit changed protected authority")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_CURRENT_STATE_AUDIT",
    "map": MAP,
    "actor_count_total": len(actors),
    "actor_count_2126": len(records),
    "class_counts": dict(sorted(class_counts.items())),
    "tag_counts": dict(sorted(tag_counts.items())),
    "records": sorted(records, key=lambda item: item["label"]),
    "static_mesh_unique_count_2126": len(mesh_instances),
    "static_mesh_instance_count_2126": sum(mesh_instances.values()),
    "static_mesh_instance_triangles_lod0_2126": instance_triangles,
    "mesh_instances": dict(sorted(mesh_instances.items())),
    "mesh_triangles_lod0": dict(sorted(mesh_triangles.items())),
    "sequence": sequence.get_path_name(),
    "sequence_binding_count": len(bindings),
    "sequence_tracks": sequence_tracks,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_CURRENT_STATE_AUDIT_PASS output=" + str(OUT))
unreal.SystemLibrary.quit_editor()
