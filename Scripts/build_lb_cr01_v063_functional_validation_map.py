"""Build v063 validation map with corrected deployed brush-carrier hierarchy."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_lb_cr01_v058_functional_validation_map.py"
code = base.read_text(encoding="utf-8")
for old, new in (
    ("Candidate_v052/Meshes", "Candidate_v059/Meshes"),
    ("v058", "v063"),
    ("V058", "V063"),
):
    code = code.replace(old, new)

old = 'material = restored_material(str(slot.get_editor_property("material_slot_name")))'
new = '''slot_name = str(slot.get_editor_property("material_slot_name"))
            material = (paint["BodyCharcoal_Restored"]
                        if name == "PVT_FrontBrushLift" and index == 0
                        else restored_material(slot_name))'''
if old not in code:
    raise RuntimeError("v063 brush-carrier material adapter drift")
code = code.replace(old, new)
exec(compile(code, str(base) + "::v063-adapter", "exec"), globals(), globals())
