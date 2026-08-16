"""Build v007 directly from v005 with the v006 camera direction and restrained exposure."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_assembly_visual_successor_v006.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v006", "v007").replace("V006", "V007")
code = code.replace("bias=1.65", "bias=1.2")
code = code.replace('"intensity", 1.4', '"intensity", 1.0')
code = code.replace('"intensity", 7.0', '"intensity", 4.0')
code = code.replace('"intensity": 7600.0', '"intensity": 4800.0')
code = code.replace('"intensity": 5200.0', '"intensity": 3400.0')
code = code.replace('"auto_exposure_bias": 1.25', '"auto_exposure_bias": 0.3')
exec(compile(code, str(base) + "::v007", "exec"), globals(), globals())

