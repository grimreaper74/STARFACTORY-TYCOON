"""Build v065 validation map with polished material family and deployed tools."""

from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_lb_cr01_v063_functional_validation_map.py"
code = base.read_text(encoding="utf-8")
for old, new in (("Candidate_v003", "Candidate_v004"), ("v063", "v065"), ("V063", "V065")):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v065-adapter", "exec"), globals(), globals())
