"""Run v037 exact gates with seven raised plates and no TextRender stage IDs."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_stage_exterior_cues_static_v037.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageExteriorCuesCandidate_v037", "LB_PressTrainARaisedIdentityCandidate_v044")
code = code.replace("press_train_a_stage_exterior_cues_static_v037", "press_train_a_raised_identity_static_v044")
code = code.replace("stage-exterior-cues-static-v037", "raised-identity-static-v044")
code = code.replace("LB.Asset.Candidate.v037", "LB.Asset.Candidate.v044")
code = code.replace("PRESS_TRAIN_A_V037", "PRESS_TRAIN_A_V044")
code = code.replace('"presentation": (len(presentation), 121)', '"presentation": (len(presentation), 128)')
code = code.replace(
    'exec(compile(code, str(base) + "::v037", "exec"), globals(), globals())',
    'code = code.replace(\'"texts": (len(texts), 13)\', \'"texts": (len(texts), 6)\')\n'
    'code = code.replace(\'"integrated_ids": (len(integrated_ids), 7)\', \'"integrated_ids": (len(integrated_ids), 0)\')\n'
    'exec(compile(code, str(base) + "::v044", "exec"), globals(), globals())')
code = code.replace("V037", "V044").replace("v037", "v044")
exec(compile(code, str(base) + "::v044", "exec"), globals(), globals())
