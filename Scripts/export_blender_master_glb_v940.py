"""Export renderable meshes from the current Blender master to a supplied GLB path."""
import bpy, sys
from pathlib import Path

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not args: raise RuntimeError("Output GLB path required")
out=Path(args[0]); out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and not o.hide_render]
for o in meshes: o.select_set(True)
if not meshes: raise RuntimeError("No renderable meshes")
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.export_scene.gltf(filepath=str(out),export_format="GLB",use_selection=True,export_apply=True,export_materials="EXPORT",export_yup=True)
print("LINE_BOSS_GLTF_EXPORT_V940",out,len(meshes),out.stat().st_size)
