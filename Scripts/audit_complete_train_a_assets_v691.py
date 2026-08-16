"""Post-repair rerun of the v688 Train A asset/performance audit."""
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir())
source_path = project / r"Scripts\audit_complete_train_a_assets_v688.py"
source = source_path.read_text(encoding="utf-8")
source = source.replace("v688", "v691").replace("V688", "V691")
exec(compile(source, str(source_path), "exec"), globals(), globals())
