"""Run the exact v005 assembly gate against the direct v007 visual successor."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_assembly_visual_static_v006.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v006", "v007").replace("V006", "V007")
exec(compile(code, str(base) + "::v007", "exec"), globals(), globals())

