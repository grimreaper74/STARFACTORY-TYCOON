"""Capture moderated-light v684 Train A visual-review map."""
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir())
source_path = project / r"Scripts\capture_complete_train_a_visual_v683.py"
source = source_path.read_text(encoding="utf-8")
source = source.replace("v682", "v684").replace("V682", "V684")
source = source.replace("v683", "v685").replace("V683", "V685")
exec(compile(source, str(source_path), "exec"), globals(), globals())
