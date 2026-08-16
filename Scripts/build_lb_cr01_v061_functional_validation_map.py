"""Adapt the proven v058 authority validation map to CR01 v061."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_lb_cr01_v058_functional_validation_map.py"
code = base.read_text(encoding="utf-8")
for old, new in (
    ("Candidate_v052/Meshes", "Candidate_v059/Meshes"),
    ("v058", "v061"),
    ("V058", "V061"),
):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v061-adapter", "exec"), globals(), globals())
