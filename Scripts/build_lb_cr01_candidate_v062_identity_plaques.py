"""Add Unreal-native Cairnwell/Moorcross identity to CR01 v060."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_lb_cr01_candidate_v055_identity_plaques.py"
code = base.read_text(encoding="utf-8")
for old, new in (
    ("v054", "v060"),
    ("V054", "V060"),
    ("v055", "v062"),
    ("V055", "V062"),
):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v062-adapter", "exec"), globals(), globals())
