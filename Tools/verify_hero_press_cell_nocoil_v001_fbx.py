"""Re-import and verify the generated coil-free press FBX in Blender."""
import json
from pathlib import Path

import bpy

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
FBX = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyNoCoil_v001" / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001.fbx"
REPORT = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyNoCoil_v001" / "Evidence" / "hero_press_cell_nocoil_v001_fbx_reimport.json"
# The source blend's evaluated loop-triangle total is 12,052.  The first probe
# included Blender's default startup cube (+12); this clean re-import removes
# it before import and verifies the FBX payload directly.
SOURCE_LOOP_TRIANGLES = 12052
EXPECTED_PAYLOAD_TRIANGLES = 12052

if not FBX.is_file():
    raise RuntimeError("Missing generated FBX")
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(FBX))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
triangles = 0
rows = []
for obj in meshes:
    mesh = obj.data
    mesh.calc_loop_triangles()
    count = len(mesh.loop_triangles)
    triangles += count
    rows.append({"name": obj.name, "triangles": count, "material_slots": [slot.material.name if slot.material else None for slot in obj.material_slots]})
corners = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
if triangles != EXPECTED_PAYLOAD_TRIANGLES:
    raise RuntimeError("Payload triangle mismatch: %d != %d" % (triangles, EXPECTED_PAYLOAD_TRIANGLES))
if len(meshes) != 2:
    raise RuntimeError("Expected body + rollers, found %d meshes" % len(meshes))
REPORT.write_text(json.dumps({
    "status": "PASS__FBX_REIMPORT_VERIFIED",
    "fbx": str(FBX),
    "source_loop_triangles_before_fbx": SOURCE_LOOP_TRIANGLES,
    "payload_triangles": triangles,
    "expected_payload_triangles": EXPECTED_PAYLOAD_TRIANGLES,
    "writer_triangulation_delta": triangles - SOURCE_LOOP_TRIANGLES,
    "meshes": rows,
    "bounds_m": {"min": [min(point[index] for point in corners) for index in range(3)], "max": [max(point[index] for point in corners) for index in range(3)]},
}, indent=2), encoding="utf-8")
print("PRESSSHOP_HERO_NOCOIL_FBX_REIMPORT_PASS")
