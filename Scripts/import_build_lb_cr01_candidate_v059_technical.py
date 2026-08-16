"""Build isolated CR01 v059 from the proven v052 technical importer."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/import_build_lb_cr01_candidate_v052_technical.py"
code = base_path.read_text(encoding="utf-8")
for old, new in (("v052", "v059"), ("V052", "V059")):
    code = code.replace(old, new)
exec(compile(code, str(base_path) + "::v059-adapter", "exec"), globals(), globals())
