"""Read-only quality audit of selected Factory Environment Collection assets.

Run this script against the vendor FactoryProject, not the Line Boss project.
It writes evidence only into the Line Boss Saved/Audits directory.
"""

import json
from pathlib import Path

import unreal


OUTPUT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Saved/Audits/factory_pack_candidates_v001.json")
CANDIDATES = {
    "cable_run": "/Game/Meshes/SM_Cables01",
    "cable_bundle": "/Game/Meshes/SM_CableSet_01",
    "electrical_cable": "/Game/Meshes/SM_ElectricalCable_01",
    "crane_cable": "/Game/Meshes/Crane/SM_CraneCable01",
    "crane_hook": "/Game/Meshes/Crane/SM_Hook01",
    "electric_motor": "/Game/Meshes/Crane/SM_ElectricMotor01",
    "round_pipe_long": "/Game/Meshes/SM_Pipe_round_long",
    "round_pipe_corner": "/Game/Meshes/SM_Pipe_round_corner1",
    "round_pipe_tee": "/Game/Meshes/SM_Pipe_round_tee_transition1",
    "guard_fence": "/Game/Meshes/SM_Fence_01",
    "guard_fence_part": "/Game/Meshes/SM_FencePart_01",
    "platform": "/Game/Meshes/SM_IndustrialPlatform01",
    "platform_railing": "/Game/Meshes/SM_PlatformRailing_01",
    "metal_beam": "/Game/Meshes/SM_MetalBeam01",
    "factory_column": "/Game/Meshes/SM_Column_02",
    "industrial_lamp": "/Game/Meshes/SM_Lamp01",
    "assembly_line_lamp": "/Game/Meshes/SM_AssemblyLineLampRamp",
    "ventilation": "/Game/Meshes/SM_CeilingVentilation01",
}

mesh_library = unreal.EditorStaticMeshLibrary
records = []
errors = []
for role, asset_path in CANDIDATES.items():
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        errors.append(f"missing static mesh: {asset_path}")
        continue
    lod_count = mesh.get_num_lods()
    vertices = [mesh.get_num_vertices(index) for index in range(lod_count)]
    triangles = [mesh.get_num_triangles(index) for index in range(lod_count)]
    uv_channels = [mesh.get_num_tex_coords(index) for index in range(lod_count)]
    bounds = mesh.get_bounds()
    extent = bounds.box_extent
    material_names = []
    for slot in mesh.get_editor_property("static_materials"):
        material = slot.get_editor_property("material_interface")
        material_names.append(material.get_path_name() if material else None)
    records.append({
        "role": role,
        "asset": asset_path,
        "lod_count": lod_count,
        "vertices_per_lod": vertices,
        "triangles_per_lod": triangles,
        "uv_channels_per_lod": uv_channels,
        "simple_collision_count": mesh_library.get_simple_collision_count(mesh),
        "convex_collision_count": mesh_library.get_convex_collision_count(mesh),
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "materials": material_names,
    })

result = {
    "status": "PASS" if not errors else "FAIL",
    "source_project": unreal.Paths.get_project_file_path(),
    "candidate_count": len(CANDIDATES),
    "loaded_count": len(records),
    "errors": errors,
    "assets": records,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if errors:
    raise RuntimeError("LINE_BOSS_FACTORY_PACK_AUDIT_FAIL " + "; ".join(errors))
unreal.log(f"LINE_BOSS_FACTORY_PACK_AUDIT_PASS assets={len(records)} output={OUTPUT}")
