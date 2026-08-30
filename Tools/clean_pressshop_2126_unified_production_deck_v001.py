"""Remove audited inherited deck clutter and add one coherent 2126 floor.

The exact 1,620 labels come from the prior read-only audit.  The deletion is
bounded by position, limited to StaticMeshActor/TextRenderActor, excludes every
2126 actor and is performed only in the isolated FullHall candidate.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
AUDIT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "clean_deck_candidate_audit_v001.json"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "clean_unified_production_deck_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.UnifiedDeck.v001")
EXPECTED_TARGETS = 1620
WARM_CONCRETE = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_WarmConcrete"
CHARCOAL = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_FoundryCharcoal"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def spawn_cube(label, location, dimensions, material, role):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None or not isinstance(cube, unreal.StaticMesh):
        raise RuntimeError("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.PressShop.2126.Architecture"), unreal.Name(role)]
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    return actor


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not AUDIT.is_file():
    raise RuntimeError("required read-only deck audit missing")
audit_hash = digest(AUDIT)
audit = json.loads(AUDIT.read_text(encoding="utf-8"))
labels = [row["label"] for row in audit.get("candidates", [])]
if audit.get("status") != "PASS_READ_ONLY" or len(labels) != EXPECTED_TARGETS or len(set(labels)) != EXPECTED_TARGETS:
    raise RuntimeError("deck audit target set is not the approved exact 1,620 unique labels")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("unified deck pass already exists")
by_label = {actor.get_actor_label(): actor for actor in actors}
missing = sorted(set(labels) - set(by_label))
if missing:
    raise RuntimeError("audited deletion targets changed or disappeared: " + repr(missing[:10]))
for label in labels:
    actor = by_label[label]
    if not isinstance(actor, (unreal.StaticMeshActor, unreal.TextRenderActor)) or label.startswith("2126"):
        raise RuntimeError("unsafe target escaped audit contract: " + label)

removed_by_class = {}
for label in labels:
    actor = by_label[label]
    class_name = actor.get_class().get_name()
    removed_by_class[class_name] = removed_by_class.get(class_name, 0) + 1
    if not unreal.EditorLevelLibrary.destroy_actor(actor):
        raise RuntimeError("could not remove audited actor " + label)

remaining_labels = {actor.get_actor_label() for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
survivors = sorted(set(labels) & remaining_labels)
if survivors:
    raise RuntimeError("audited clutter survived deletion: " + repr(survivors[:10]))
preserved_2126 = sorted(label for label in remaining_labels if label.startswith("2126"))
if len(preserved_2126) < 50:
    raise RuntimeError("2126 production set unexpectedly reduced: %d" % len(preserved_2126))

warm_concrete = unreal.load_asset(WARM_CONCRETE)
charcoal = unreal.load_asset(CHARCOAL)
if not all(isinstance(material, unreal.MaterialInterface) for material in (warm_concrete, charcoal)):
    raise RuntimeError("unified deck materials missing")

created = []
created.append(spawn_cube(
    "2126 FLOOR | unified warm-concrete production deck",
    (-1250.0, 750.0, -6.0), (18500.0, 11500.0, 10.0), warm_concrete, "LB.Architecture.Floor").get_actor_label())
# Two low charcoal datum strips frame the clean gameplay area without a roof.
created.append(spawn_cube(
    "2126 FLOOR | west charcoal boundary datum",
    (-10390.0, 750.0, 1.0), (120.0, 11500.0, 12.0), charcoal, "LB.Architecture.Boundary").get_actor_label())
created.append(spawn_cube(
    "2126 FLOOR | east charcoal boundary datum",
    (7890.0, 750.0, 1.0), (120.0, 11500.0, 12.0), charcoal, "LB.Architecture.Boundary").get_actor_label())

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save unified production deck")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during unified deck cleanup")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_UNIFIED_PRODUCTION_DECK_REPLACED_AUDITED_CLUTTER",
    "map": MAP,
    "audit": str(AUDIT),
    "audit_sha256": audit_hash,
    "removed_count": len(labels),
    "removed_by_class": removed_by_class,
    "preserved_2126_actor_count_before_floor_creation": len(preserved_2126),
    "created": created,
    "roof_created": False,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_UNIFIED_DECK_PASS removed=%d" % len(labels))
unreal.SystemLibrary.quit_editor()
