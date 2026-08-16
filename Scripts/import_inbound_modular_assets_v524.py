"""Import additive inbound Modular_v005 into an isolated Unreal folder."""
from pathlib import Path
source = (Path(__file__).parent / "import_inbound_modular_assets_v506.py").read_text(encoding="utf-8")
source = source.replace("Modular_v004", "Modular_v005").replace("Candidate_v004", "Candidate_v005")
source = source.replace("_v004", "_v005").replace("v004", "v005")
source = source.replace("v506", "v524").replace("V506", "V524")
# Candidate_v005 adds the powered restraint hook and lock indicator above the
# previous dock-guide envelope.  Keep the scale guard, but admit that intended
# additive height.  A prior interrupted run may also have left assets in this
# isolated candidate folder, so replacing them here is safe and deterministic.
source = source.replace("(50, 100)),", "(50, 125)),", 1)
source = source.replace('"replace_existing": False', '"replace_existing": True')
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
