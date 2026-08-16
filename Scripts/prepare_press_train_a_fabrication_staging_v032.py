"""Correct v031's centimetre export scale in a fresh v032 staging lineage."""

from pathlib import Path


source = Path(__file__).with_name("prepare_press_train_a_fabrication_staging_v031.py")
code = source.read_text(encoding="utf-8").replace("v031", "v032").replace("V031", "V032")
code = code.replace("import bpy\n", "import bpy\nfrom mathutils import Matrix\n", 1)
needle = "    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)\n    duplicate = bpy.data.objects.new(asset_name, mesh)"
replacement = "    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)\n    # The retained Unreal assets use centimetre vertex space.  v031 proved that\n    # direct metre-space export imports at exactly 1/100 scale.\n    mesh.transform(Matrix.Scale(100.0, 4))\n    duplicate = bpy.data.objects.new(asset_name, mesh)"
if needle not in code:
    raise RuntimeError("v031 scale correction insertion point changed")
code = code.replace(needle, replacement, 1)
exec(compile(code, str(source) + "::correct-centimetre-scale-v032", "exec"), {
    "__name__": "__main__",
    "__file__": str(source).replace("v031", "v032"),
})
