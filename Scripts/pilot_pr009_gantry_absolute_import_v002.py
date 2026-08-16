"""Compare uncombined PR-009 gantry import with FBX node transforms baked absolute."""
from pathlib import Path

base = Path(__file__).with_name("pilot_pr009_gantry_decomposition_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("DecompositionPilot_v001/Gantry", "DecompositionPilot_v002/GantryAbsolute")
code = code.replace("gantry_decomposition_pilot_v001.json", "gantry_absolute_import_pilot_v002.json")
code = code.replace('("transform_vertex_to_absolute", False)', '("transform_vertex_to_absolute", True)')
code = code.replace("pr009-gantry-decomposition-pilot-v001", "pr009-gantry-absolute-import-pilot-v002")
code = code.replace("PR009_GANTRY_UNCOMBINED_IMPORT_OBJECT_COUNT_AND_ASSEMBLED_BOUNDS_PASS", "PR009_GANTRY_ABSOLUTE_UNCOMBINED_IMPORT_OBJECT_COUNT_AND_ASSEMBLED_BOUNDS_PASS")
code = code.replace("PR009_GANTRY_UNCOMBINED_IMPORT_PILOT_FAIL", "PR009_GANTRY_ABSOLUTE_UNCOMBINED_IMPORT_PILOT_FAIL")
exec(compile(code, str(base) + "::absolute-v002", "exec"), globals(), globals())
