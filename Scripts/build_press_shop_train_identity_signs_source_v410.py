"""Non-overwriting v410 readable sign source with corrected text normals."""
from pathlib import Path
source=Path(__file__).with_name("build_press_shop_train_identity_signs_source_v396.py")
code=source.read_text(encoding="utf-8")
code=code.replace("import bpy\n", "import bpy\nimport bmesh\n", 1)
code=code.replace("PhysicalSigns_v396","PhysicalSigns_v410")
code=code.replace("v396","v410")
old="""    for vertex in obj.data.vertices:\n        x, y, z = vertex.co\n        vertex.co = (-z - 0.055, x + centre_y_mm / 1000.0, y + centre_z_mm / 1000.0)\n    parts.append(obj)"""
new="""    for vertex in obj.data.vertices:\n        x, y, z = vertex.co\n        vertex.co = (-z - 0.088, -x + centre_y_mm / 1000.0, y + centre_z_mm / 1000.0)\n    bm = bmesh.new()\n    bm.from_mesh(obj.data)\n    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)\n    bm.to_mesh(obj.data)\n    bm.free()\n    obj.data.update()\n    parts.append(obj)"""
code=code.replace(old,new)
if "bmesh.ops.recalc_face_normals" not in code:raise RuntimeError("v410 normal correction substitution failed")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
