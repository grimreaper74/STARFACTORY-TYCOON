"""Apply the v058 material policy to direct-from-v053 low-profile coupling v059."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_reference_finish_candidate_v058.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    'import_build_press_train_a_dock_coupling_candidate_v057.py',
    'import_build_press_train_a_dock_coupling_candidate_v059.py',
)
code = code.replace("Candidate_v058", "Candidate_v059")
code = code.replace("reference_finish_v058", "reference_finish_v059")
code = code.replace("reference-finish-v058", "reference-finish-v059")
code = code.replace("LB.Asset.Candidate.v058", "LB.Asset.Candidate.v059")
code = code.replace("PRESS_TRAIN_A_V058", "PRESS_TRAIN_A_V059")
code = code.replace("V058", "V059").replace("v058", "v059")
exec(compile(code, str(base) + "::v059", "exec"), globals(), globals())
