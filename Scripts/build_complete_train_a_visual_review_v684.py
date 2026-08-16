"""Moderated-light derivative of v682 after its capture proved overexposed."""
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir())
source_path = project / r"Scripts\build_complete_train_a_visual_review_v682.py"
source = source_path.read_text(encoding="utf-8")
source = source.replace("v682", "v684").replace("V682", "V684")
source = source.replace('"intensity": 220000.0', '"intensity": 8000.0')
source = source.replace('"intensity": 3.5', '"intensity": 1.5')
source = source.replace('"auto_exposure_bias": 0.75', '"auto_exposure_bias": -1.0')
exec(compile(source, str(source_path), "exec"), globals(), globals())
