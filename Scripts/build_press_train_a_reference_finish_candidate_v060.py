"""Apply the v058 material policy to direct-from-v053 coupling-v003 v060."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_reference_finish_candidate_v058.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    'import_build_press_train_a_dock_coupling_candidate_v057.py',
    'import_build_press_train_a_dock_coupling_candidate_v060.py',
)
code = code.replace("Candidate_v058", "Candidate_v060")
code = code.replace("reference_finish_v058", "reference_finish_v060")
code = code.replace("reference-finish-v058", "reference-finish-v060")
code = code.replace("LB.Asset.Candidate.v058", "LB.Asset.Candidate.v060")
code = code.replace("PRESS_TRAIN_A_V058", "PRESS_TRAIN_A_V060")
code = code.replace("V058", "V060").replace("v058", "v060")
exec(compile(code, str(base) + "::v060", "exec"), globals(), globals())
