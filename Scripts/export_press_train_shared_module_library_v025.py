"""Correct v024 by excluding the hidden combined review/export mesh."""
from pathlib import Path

base=Path(__file__).with_name("export_press_train_shared_module_library_v024.py")
code=base.read_text(encoding="utf-8")
code=code.replace("PressBodyModuleLibrary_v024", "PressBodyModuleLibrary_v025")
code=code.replace("PRESS_BODY_MODULE_LIBRARY_MANIFEST_v024", "PRESS_BODY_MODULE_LIBRARY_MANIFEST_v025")
code=code.replace("PRESS_BODY_MODULE_LIBRARY_VALIDATION_v024", "PRESS_BODY_MODULE_LIBRARY_VALIDATION_v025")
code=code.replace("_v024", "_v025").replace("-v024", "-v025")
code=code.replace(
    'objects=[o for o in groups[k].objects if o.type in {"MESH","CURVE","FONT"}]',
    'objects=[o for o in groups[k].objects if o.type in {"MESH","CURVE","FONT"} and not o.name.startswith("SM_CA_MW_PressModulePrototype_")]'
)
exec(compile(code,str(base)+"::v025","exec"),globals(),globals())
