"""Create CR01 v063 authority with v062 branded scrubber presentation."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_lb_cr01_candidate_v061_functional_authority.py"
code = base.read_text(encoding="utf-8")
for old, new in (
    ("v060", "v062"),
    ("V060", "V062"),
    ("v061", "v063"),
    ("V061", "V063"),
):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v063-adapter", "exec"), globals(), globals())
