"""Correct v657's UE 5.8 component move signature; preserve v657 evidence."""
from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir())
source=(project/r"Scripts\import_build_complete_s03_modular_v655.py").read_text(encoding="utf-8")
source=source.replace("CompleteS03Modular_v654","CompleteS03Modular_v656")
source=source.replace("complete_s03_modular_staging_v654","complete_s03_modular_staging_v656")
source=source.replace("set_relative_location(unreal.Vector(*component_offset))",
 "set_relative_location(unreal.Vector(*component_offset),False,False)")
source=source.replace("v655","v658").replace("V655","V658")
exec(compile(source,str(project/r"Scripts\import_build_complete_s03_modular_v655.py"),"exec"),globals(),globals())
