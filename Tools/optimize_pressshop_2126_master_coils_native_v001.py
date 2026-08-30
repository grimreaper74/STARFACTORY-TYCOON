"""Localise the approved master coil for native Unreal runtime rendering.

The source mesh remains untouched.  A candidate-local byte-derived duplicate
retains the exact 78,758-triangle geometry and ten material slots, gains Nanite
data, and replaces only the eight FullHall coil actors.  Their hard shadows are
disabled to match the shadowless fixed-angle machinery sprites.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
SOURCE = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
DEST = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Meshes/SM_CA_MW_2126_MasterCoil_Nanite_v001"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "IndustrialKit" / "MaterialHandling" / "MasterCoil" / "Candidate_v005" / "SM_LB_MasterCoil_Candidate_v005.uasset"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "master_coils_native_optimization_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.CoilRuntime.v001")
COILS = (
    "2126 LOG | delivery coil 02 | approved packaged master coil",
    "2126 LOG | delivery coil 03 | approved packaged master coil",
    "2126 LOG | delivery coil 04 | approved packaged master coil",
    "2126 LOG | coil 01 mid-transfer under autonomous gantry",
    "2126 COIL | verification cell active load",
    "2126 COIL | magnetic buffer load A",
    "2126 COIL | magnetic buffer load C",
    "2126 FRONT END | active feed coil",
)
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not SOURCE_FILE.is_file():
    raise RuntimeError("approved source coil file missing")
source_hash = digest(SOURCE_FILE)
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError("candidate-local coil already exists; refusing overwrite")

source = unreal.load_asset(SOURCE)
if not isinstance(source, unreal.StaticMesh):
    raise RuntimeError("approved source coil asset missing")
if int(source.get_num_triangles(0)) != 78758 or int(source.get_num_lods()) != 1:
    raise RuntimeError("approved source coil topology changed")
if len(source.get_editor_property("static_materials")) != 10:
    raise RuntimeError("approved source coil slot contract changed")

runtime_mesh = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
if not isinstance(runtime_mesh, unreal.StaticMesh):
    raise RuntimeError("could not duplicate approved coil into candidate")
if int(runtime_mesh.get_num_triangles(0)) != int(source.get_num_triangles(0)):
    raise RuntimeError("candidate-local duplicate changed coil geometry")
if len(runtime_mesh.get_editor_property("static_materials")) != 10:
    raise RuntimeError("candidate-local duplicate changed material slots")

mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
settings = mesh_editor.get_nanite_settings(runtime_mesh)
settings.enabled = True
settings.lerp_u_vs = True
settings.keep_percent_triangles = 1.0
settings.fallback_percent_triangles = 1.0
mesh_editor.set_nanite_settings(runtime_mesh, settings, True)
verified_settings = mesh_editor.get_nanite_settings(runtime_mesh)
if not verified_settings.enabled:
    raise RuntimeError("Nanite did not enable on candidate-local coil")
if not unreal.EditorAssetLibrary.save_loaded_asset(runtime_mesh, only_if_is_dirty=False):
    raise RuntimeError("candidate-local coil asset did not save")

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("coil runtime pass already tagged")

rows = []
for label in COILS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("placed master coil missing: " + label)
    component = actor.static_mesh_component
    overrides = [component.get_material(index) for index in range(component.get_num_materials())]
    if len(overrides) != 10 or any(material is None for material in overrides):
        raise RuntimeError("placed coil material overrides incomplete: " + label)
    component.set_static_mesh(runtime_mesh)
    for index, material in enumerate(overrides):
        component.set_material(index, material)
    component.set_editor_property("cast_shadow", False)
    component.set_editor_property("cast_dynamic_shadow", False)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Role.NaniteRuntimeCoil")]
    rows.append({
        "label": label,
        "mesh": component.static_mesh.get_path_name(),
        "material_slots": component.get_num_materials(),
        "cast_shadow": bool(component.get_editor_property("cast_shadow")),
    })

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save candidate coil runtime pass")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during coil runtime pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_COILS_LOCALIZED_NANITE_AND_SHADOW_BALANCED",
    "map": MAP,
    "source_asset": source.get_path_name(),
    "source_file_sha256": source_hash,
    "runtime_asset": runtime_mesh.get_path_name(),
    "source_geometry_preserved": True,
    "triangles_lod0": int(runtime_mesh.get_num_triangles(0)),
    "material_slot_count": len(runtime_mesh.get_editor_property("static_materials")),
    "nanite_enabled": bool(verified_settings.enabled),
    "fallback_percent_triangles": float(verified_settings.fallback_percent_triangles),
    "placed_coil_count": len(rows),
    "placed_coils": rows,
    "cast_shadow_disabled_for_fixed_angle_consistency": True,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_COIL_NATIVE_OPTIMIZATION_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
