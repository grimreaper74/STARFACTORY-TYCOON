"""Import the read-only retained v301 Train A FBX into a new Blender reference file."""
from __future__ import annotations

import sys
from pathlib import Path

import bpy


args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(args) != 2:
    raise RuntimeError("Expected input FBX and output BLEND after --")
source = Path(args[0]).resolve()
output = Path(args[1]).resolve()
if not source.is_file():
    raise FileNotFoundError(source)
if output.exists():
    raise FileExistsError(f"Refusing to overwrite {output}")
output.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for datablock in list(datablocks):
        if datablock.users == 0:
            datablocks.remove(datablock)

result = bpy.ops.wm.fbx_import(filepath=str(source), use_custom_normals=True)
if "FINISHED" not in result:
    raise RuntimeError(f"FBX import failed: {result}")
imported = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE", "FONT"}]
if not imported:
    raise RuntimeError("FBX import produced no renderable objects")

bpy.context.scene["LB_REFERENCE_ONLY"] = True
bpy.context.scene["LB_SOURCE_FBX"] = str(source)
bpy.context.scene["LB_IMPORTED_OBJECT_COUNT"] = len(imported)
bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
print(f"LB_RETAINED_TRAIN_A_BLENDER_IMPORT_PASS objects={len(imported)} output={output}")
