"""Build v008 directly from v005 with balanced low-key evidence lighting."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_assembly_visual_successor_v006.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v006", "v008").replace("V006", "V008")
code = code.replace("bias=1.65", "bias=0.7")
code = code.replace('"intensity", 1.4', '"intensity", 0.7')
code = code.replace('"intensity", 7.0', '"intensity", 3.0')
code = code.replace('"intensity": 7600.0', '"intensity": 3000.0')
code = code.replace('"intensity": 5200.0', '"intensity": 2200.0')
code = code.replace('"auto_exposure_bias": 1.25', '"auto_exposure_bias": 0.1')
exec(compile(code, str(base) + "::v008", "exec"), globals(), globals())

