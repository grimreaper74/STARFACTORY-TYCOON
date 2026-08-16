"""Axis-corrected non-overwriting successor to rejected v031."""
from pathlib import Path
base=Path(__file__).with_name("assemble_press_train_a_modular_source_v031.py")
code=base.read_text(encoding="utf-8")
code=code.replace("ModularAssembly_v031","ModularAssembly_v032").replace("MODULAR_ASSEMBLY_MANIFEST_v031","MODULAR_ASSEMBLY_MANIFEST_v032").replace("MODULAR_ASSEMBLY_VALIDATION_v031","MODULAR_ASSEMBLY_VALIDATION_v032").replace("_v031","_v032").replace("-v031","-v032")
old='stages[stage].objects.link(o);o.location.y+=DATUMS[stage];o.name=f"PTA_{stage}_{role}_{o.name}_v032";'
new='stages[stage].objects.link(o);\n  if stage in {"S02","S03","S04","S05","S06"}: o.rotation_euler.z+=math.pi/2; o.location=Vector((-o.location.y,o.location.x+DATUMS[stage],o.location.z))\n  else: o.location.y+=DATUMS[stage]\n  o.name=f"PTA_{stage}_{role}_{o.name}_v032";'
if old not in code: raise RuntimeError("v031 import transform anchor changed")
code=code.replace(old,new)
code=code.replace('"status":"SOURCE_ONLY_COMPLETE_SEVEN_STATION_MODULAR_ASSEMBLY__FRESH_VISUAL_DECISION_REQUIRED__NOT_PROMOTED"', '"status":"SOURCE_ONLY_AXIS_CORRECTED_COMPLETE_SEVEN_STATION_MODULAR_ASSEMBLY__FRESH_VISUAL_DECISION_REQUIRED__NOT_PROMOTED"')
exec(compile(code,str(base)+"::v032","exec"),globals(),globals())
