"""Independent clean-scene FBX audit for PR-004 FilmDewrapSpindle v007."""

from pathlib import Path


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = REPO / "Scripts/audit_pr004_film_dewrap_spindle_candidate_v006_independent.py"
source = SOURCE.read_text(encoding="utf-8")
source = source.replace("FilmDewrapSpindle_v006", "FilmDewrapSpindle_v007")
source = source.replace("film_dewrap_spindle_candidate_v006", "film_dewrap_spindle_candidate_v007")
source = source.replace("_v006", "_v007")
source = source.replace('"v006"', '"v007"')
exec(
    compile(source, str(SOURCE), "exec"),
    {"__name__": "__main__", "__file__": str(Path(__file__).resolve())},
)
