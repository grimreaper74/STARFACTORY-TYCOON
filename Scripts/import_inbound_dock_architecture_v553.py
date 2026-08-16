"""Isolated Unreal intake for additive inbound dock architecture v002."""
from pathlib import Path

root = Path(__file__).parent
source = (root / "import_inbound_dock_architecture_v536.py").read_text(encoding="utf-8")
source = source.replace("DockArchitecture_v001", "DockArchitecture_v002")
source = source.replace("DockArchitectureCandidate_v001", "DockArchitectureCandidate_v002")
source = source.replace("SM_CA_MW_Inbound_DockArchitecture_v001", "SM_CA_MW_Inbound_DockArchitecture_v002")
source = source.replace("v536", "v553").replace("V536", "V553")
exec(compile(source, str(root / "import_inbound_dock_architecture_v536.py"), "exec"), globals(), globals())
