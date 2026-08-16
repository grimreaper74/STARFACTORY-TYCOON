"""Run the v651 isolated intake contract against corrected v652 staging."""
from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir())
source=(project/r"Scripts\import_build_complete_s03_isolated_v651.py").read_text(encoding="utf-8")
source=source.replace("CompleteS03_v650","CompleteS03_v652")
source=source.replace("CompleteVisual_v650","CompleteVisual_v652")
source=source.replace("v651","v653").replace("V651","V653")
exec(compile(source,str(project/r"Scripts\import_build_complete_s03_isolated_v651.py"),"exec"),globals(),globals())
