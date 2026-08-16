"""Build warning-clean low-profile dock/manifold source v003."""

import ast
from pathlib import Path


v001 = Path(__file__).with_name("build_press_train_dock_coupling_evidence_v001.py")
v002 = Path(__file__).with_name("build_press_train_dock_coupling_evidence_v002.py")
tree = ast.parse(v002.read_text(encoding="utf-8"))
geometry = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "geometry" for t in node.targets):
        geometry = ast.literal_eval(node.value)
        break
if geometry is None:
    raise RuntimeError("could not recover v002 low-profile geometry block")

code = v001.read_text(encoding="utf-8").replace("v001", "v003").replace("V001", "V003")
start = code.index("# Two visible hydraulic lock bridges")
end = code.index('bpy.ops.object.select_all(action="DESELECT")', start)
code = code[:start] + geometry + code[end:]
code = code.replace(
    '"planning_envelope_mm": [1800, 3700, 1800]',
    '"planning_envelope_mm": [1500, 3200, 1000]',
)
normal_fix = '''
# Unreal import-quality preparation: flatten shading, recalculate outward
# normals and triangulate the final joined mesh before FBX export.
for polygon in asset.data.polygons:
    polygon.use_smooth = False
bpy.context.view_layer.objects.active = asset
asset.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")
triangulate = asset.modifiers.new("TriangulateForUnreal", "TRIANGULATE")
triangulate.keep_custom_normals = True
bpy.context.view_layer.objects.active = asset
bpy.ops.object.modifier_apply(modifier=triangulate.name)

'''
code = code.replace("fbx_path = FBX / f\"{asset.name}.fbx\"", normal_fix + "fbx_path = FBX / f\"{asset.name}.fbx\"")
code = code.replace(
    '"notes": "Camera-readable engaged-state evidence only; runtime separation and interlock ownership remain mandatory before promotion."',
    '"notes": "Warning-clean low-profile engaged dock/manifold evidence below cart deck; runtime separation and interlock ownership remain mandatory before promotion."',
)
exec(compile(code, str(v001) + "::v003", "exec"), globals(), globals())
