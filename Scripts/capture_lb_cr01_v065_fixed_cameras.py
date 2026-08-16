"""Capture one CR01 v065 fixed camera per process."""

from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
base = root / "Scripts/capture_lb_cr01_v063_fixed_cameras.py"
code = base.read_text(encoding="utf-8")
for old, new in (("v063", "v065"), ("V063", "V065"), ("branded_scrubber", "polished_scrubber"), ("branded scrubber", "polished scrubber")):
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v065-adapter", "exec"), globals(), globals())
