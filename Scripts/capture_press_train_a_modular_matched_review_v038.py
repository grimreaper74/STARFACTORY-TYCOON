"""Matched review of identity-corrected Train A v037."""
from pathlib import Path
base=Path(__file__).with_name("capture_press_train_a_modular_matched_review_v033.py")
code=base.read_text(encoding="utf-8")
code=code.replace("ModularAssembly_v033/CA_MW_PressTrainA_ModularAssembly_v033.blend","ModularAssembly_v037/CA_MW_PressTrainA_ModularAssembly_v037.blend")
code=code.replace('OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/MatchedReview"','OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/MatchedReview_v038"')
code=code.replace("MATCHED_REVIEW_v033","MATCHED_REVIEW_v038").replace("matched-review-v033","matched-review-v038")
code=code.replace('f"train_a_matched_{name}_v033.png"','f"train_a_matched_{name}_v038.png"')
code=code.replace("    cam.rotation_euler.z = roll\n","    if name == \"top\":\n        cam.rotation_euler.z += roll\n")
code=code.replace("refusing to overwrite v033 matched review","refusing to overwrite v038 matched review")
exec(compile(code,str(base)+"::v038","exec"),globals(),globals())
