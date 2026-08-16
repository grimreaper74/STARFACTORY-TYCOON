"""Correct v039's stage-tag resolver and build the identity treatment as v040."""

from pathlib import Path

base = Path(__file__).with_name("correct_press_train_a_integrated_identity_candidate_v039.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAIntegratedIdentityCandidate_v039", "LB_PressTrainAIntegratedIdentityCandidate_v040")
code = code.replace("press_train_a_integrated_identity_v039", "press_train_a_integrated_identity_v040")
code = code.replace("integrated-identity-v039", "integrated-identity-v040")
code = code.replace("LB.Asset.Candidate.v039", "LB.Asset.Candidate.v040")
code = code.replace("V039", "V040").replace("v039", "v040")
code = code.replace(
    'next((value for value in short_names if f".{value}.IntegratedIdentity" in tag_set), None)',
    'next((value for value in short_names if f"LB.PressTrain.EnclosedFacade.{value}.IntegratedIdentity" in tag_set), None)')
exec(compile(code, str(base) + "::v040", "exec"), globals(), globals())
