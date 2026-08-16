"""Create CR01 v065 authority with v064 polished scrubber presentation."""

from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
base = root / "Scripts/build_lb_cr01_candidate_v061_functional_authority.py"
code = base.read_text(encoding="utf-8")
for old, new in (("v060", "v064"), ("V060", "V064"), ("v061", "v065"), ("V061", "V065")):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v065-adapter", "exec"), globals(), globals())
