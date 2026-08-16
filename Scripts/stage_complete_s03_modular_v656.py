"""Correct v654 local-pivot FBX units; v654/v655 remain failed evidence."""
from pathlib import Path
source=(Path(__file__).with_name("stage_complete_s03_modular_v654.py").read_text(encoding="utf-8"))
source=source.replace("CompleteS03Modular_v654","CompleteS03Modular_v656")
source=source.replace("complete_s03_modular_staging_v654","complete_s03_modular_staging_v656")
source=source.replace("_v654", "_v656").replace('"v654"','"v656"')
source=source.replace(
 'bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={"MESH"},global_scale=1.0,\n  apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",',
 'obj.data.transform(Matrix.Scale(100.0,4))\n bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={"MESH"},global_scale=1.0,\n  apply_unit_scale=False,apply_scale_options="FBX_SCALE_NONE",axis_forward="-Z",axis_up="Y",')
source=source.replace('"bounds_m":[round(v,4) for v in obj.dimensions]', '"bounds_m":[round(v/100.0,4) for v in obj.dimensions]')
exec(compile(source,str(Path(__file__).with_name("stage_complete_s03_modular_v654.py")),"exec"),globals(),globals())
