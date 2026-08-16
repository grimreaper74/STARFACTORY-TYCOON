"""Isolated Unreal intake for the selected PR005 visual skin derivative.

This imports four static, visual-only meshes and five simple controlled palette materials
into a new candidate namespace. It does not edit maps, runtime bindings, gameplay, saves,
collision authority, source assets, or v913.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_ROOT = ROOT / "SourceAssets/Candidate/PressShop/PR005/SkinRuntimeCandidate_v001"
MANIFEST_PATH = SOURCE_ROOT / "PR005_SkinRuntimeCandidate_v001_manifest.json"
DESTINATION = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/SkinRuntime_v001"
MESH_DESTINATION = DESTINATION + "/StaticMeshes"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
AUDIT = ROOT / "Saved/Audits/PR005/SkinRuntime_v001/pr005_skin_runtime_intake_v001.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
materials = unreal.MaterialEditingLibrary


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def asset_name_from_fbx(relative_fbx: str) -> str:
    return Path(relative_fbx).stem


def create_material(name: str, colour: tuple[float, float, float], roughness: float, metallic: float) -> unreal.Material:
    asset_path = f"{MATERIAL_DESTINATION}/{name}"
    if library.does_asset_exist(asset_path):
        raise RuntimeError(f"fresh-material invariant failed: {asset_path}")
    material = asset_tools.create_asset(name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create material {asset_path}")
    base = materials.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, 0)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = materials.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 140)
    rough.set_editor_property("r", roughness)
    metal = materials.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 250)
    metal.set_editor_property("r", metallic)
    materials.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    materials.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    materials.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    materials.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def import_mesh(source: Path, name: str) -> unreal.StaticMesh:
    expected_path = f"{MESH_DESTINATION}/{name}"
    if library.does_asset_exist(expected_path):
        raise RuntimeError(f"fresh-mesh invariant failed: {expected_path}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": MESH_DESTINATION,
        "destination_name": name,
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
    })
    task.options = options
    asset_tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = library.load_asset(expected_path)
    if not isinstance(mesh, unreal.StaticMesh):
        imported = list(task.get_editor_property("imported_object_paths"))
        raise RuntimeError(f"static mesh missing for {source}; imported={imported}")
    # Nanite is intentionally not assumed for a low-triangle overview skin. It remains
    # disabled until a later render/performance gate proves a benefit.
    static_materials = mesh.get_editor_property("static_materials")
    if not static_materials:
        raise RuntimeError(f"material-slot import failed for {mesh.get_path_name()}")
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    return mesh


def bound_record(mesh: unreal.StaticMesh) -> dict:
    box = mesh.get_bounding_box()
    return {
        "min_cm": [round(box.min.x, 4), round(box.min.y, 4), round(box.min.z, 4)],
        "max_cm": [round(box.max.x, 4), round(box.max.y, 4), round(box.max.z, 4)],
        "size_cm": [round(box.max.x - box.min.x, 4), round(box.max.y - box.min.y, 4), round(box.max.z - box.min.z, 4)],
    }


if not MANIFEST_PATH.is_file():
    raise RuntimeError(f"missing derivative manifest: {MANIFEST_PATH}")
if library.does_asset_exist(DESTINATION):
    raise RuntimeError(f"fresh candidate namespace already exists: {DESTINATION}")

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
if manifest.get("status") != "CANDIDATE_ONLY__SOURCE_DERIVATIVE_COMPLETE__UNREAL_INTAKE_NOT_STARTED":
    raise RuntimeError(f"source candidate not in intake state: {manifest.get('status')}")
if manifest.get("visual_source_sha256_before") != manifest.get("visual_source_sha256_after"):
    raise RuntimeError("visual source immutability gate failed")
if manifest.get("engineering_authority_sha256_before") != manifest.get("engineering_authority_sha256_after"):
    raise RuntimeError("engineering authority immutability gate failed")

palette = {
    "M_CA_MW_PR005_Skin_WarmWhite_v001": ((0.8963, 0.8800, 0.8148), 0.32, 0.35),
    "M_CA_MW_PR005_Skin_Graphite_v001": ((0.0152, 0.0176, 0.0200), 0.30, 0.66),
    "M_CA_MW_PR005_Skin_CairnwellGreen_v001": ((0.0137, 0.0704, 0.0600), 0.34, 0.42),
    "M_CA_MW_PR005_Skin_SafetyYellow_v001": ((0.8879, 0.5457, 0.0), 0.36, 0.30),
    "M_CA_MW_PR005_Skin_ExposedSteel_v001": ((0.1620, 0.1850, 0.2051), 0.26, 0.84),
    "M_CA_MW_PR005_Skin_EStopRed_v001": ((0.6584, 0.0203, 0.0203), 0.30, 0.24),
}
created_materials = {name: create_material(name, *values) for name, values in palette.items()}

mesh_records = []
for export in manifest["exports"]:
    fbx = SOURCE_ROOT / export["fbx"]
    if not fbx.is_file():
        raise RuntimeError(f"missing FBX {fbx}")
    source_hash_before = sha256(fbx)
    if source_hash_before != export["sha256"]:
        raise RuntimeError(f"FBX source hash mismatch: {fbx}")
    name = asset_name_from_fbx(export["fbx"])
    mesh = import_mesh(fbx, name)
    # Maps imported Blender semantic material slots to separately built, controlled UE PBR.
    for index, static_material in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(static_material.material_slot_name)
        material_name = slot_name
        material = created_materials.get(material_name)
        if material is None:
            raise RuntimeError(f"unexpected imported material slot {slot_name} on {mesh.get_path_name()}")
        mesh.set_material(index, material)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    source_hash_after = sha256(fbx)
    if source_hash_after != source_hash_before:
        raise RuntimeError(f"FBX mutated during import: {fbx}")
    mesh_records.append({
        "source_fbx": str(fbx.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "asset": mesh.get_path_name(),
        "bounds": bound_record(mesh),
        "material_slots": [
            {
                "slot_name": str(slot.material_slot_name),
                "material": slot.material_interface.get_path_name() if slot.material_interface else "",
            }
            for slot in mesh.get_editor_property("static_materials")
        ],
        "collision_policy": "NO_AUTO_COLLISION__RUNTIME_COMPONENT_MUST_BE_NO_COLLISION_NO_NAV_NO_OVERLAPS",
        "nanite_policy": "DISABLED_PENDING_RENDER_PERFORMANCE_GATE",
    })

library.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
report = {
    "$schema": "cairnwell/pr005-skin-runtime-intake-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_ONLY__ISOLATED_UNREAL_INTAKE_PASS__NO_RUNTIME_BINDING",
    "source_derivative_manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
    "source_authority_immutable": True,
    "destination": DESTINATION,
    "meshes": mesh_records,
    "materials": {name: material.get_path_name() for name, material in created_materials.items()},
    "collision": "not generated; visual-only components required",
    "pivots": "no runtime pivots/sockets; static overlay only",
    "nanite": "disabled pending overview render and performance validation",
    "save_gameplay_map_v913": "unchanged",
    "next_gate": "add isolated components, compile, real HUD overview, then regression/functional/cook validation",
}
AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_SKIN_RUNTIME_INTAKE_PASS {AUDIT}")
