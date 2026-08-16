"""Independently re-import and audit the packaged-coil v004 FBX."""

from pathlib import Path
import json

import bpy


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
FBX = REPO / "SourceAssets/IndustrialKit/MasterCoil/Candidate_v004/SM_LB_MasterCoil_Candidate_v004.fbx"
OUT = REPO / "Saved/Audits/packaged_coil_v004_fbx.json"
RENDER = "SM_LB_MasterCoil_Candidate_v004"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(FBX), use_custom_normals=True)

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
render = next((obj for obj in meshes if obj.name == RENDER), None)
ucx = sorted(obj.name for obj in meshes if obj.name.startswith("UCX_" + RENDER))
if render is None:
    raise RuntimeError("render mesh missing after clean FBX import")

triangles = sum(max(0, len(poly.vertices) - 2) for poly in render.data.polygons)
result = {
    "status": "PASS" if len(ucx) == 12 else "FAIL",
    "fbx": str(FBX),
    "render_mesh": render.name,
    "bounds_xyz_cm": [round(value * 100.0, 3) for value in render.dimensions],
    "vertices": len(render.data.vertices),
    "triangles": triangles,
    "material_slots": len(render.material_slots),
    "ucx_count": len(ucx),
    "ucx_names": ucx,
    "fbx_mesh_nodes": [
        {"object": obj.name, "mesh_data": obj.data.name}
        for obj in sorted(meshes, key=lambda item: item.name)
    ],
    "requirements": {
        "bounds_xyz_cm": [149.98, 190.0, 190.0],
        "ucx_count": 12,
        "clear_collision_bore_mm": 640.0,
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if result["status"] != "PASS":
    raise RuntimeError(f"FBX audit failed: {result}")
print(
    "PACKAGED_COIL_V004_FBX_AUDIT_PASS "
    f"bounds_cm={result['bounds_xyz_cm']} tris={triangles} "
    f"materials={result['material_slots']} ucx={len(ucx)}"
)
