"""Read-only Meshy material-slot audit for the clean Press Shop v002 map."""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_meshy_slot_audit_v010.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")

rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("MESHY v002 | ") and "coil-free autonomous feeder" not in label:
        continue
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected static mesh actor: " + label)
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    slots = []
    for index, static_material in enumerate(mesh.get_editor_property("static_materials")):
        override = component.get_material(index)
        slots.append({
            "index": index,
            "source_slot": str(static_material.get_editor_property("material_slot_name")),
            "source_material": static_material.get_editor_property("material_interface").get_path_name() if static_material.get_editor_property("material_interface") else None,
            "instance_override": override.get_path_name() if override else None,
        })
    rows.append({"label": label, "mesh": mesh.get_path_name(), "slots": slots})

if len(rows) != 6:
    raise RuntimeError("Expected five presses and one feeder; found %d" % len(rows))
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Read-only audit changed protected v438")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_MESHY_SLOT_AUDIT",
    "candidate_map": MAP,
    "actors": rows,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_MESHY_SLOT_AUDIT_V010_PASS")
