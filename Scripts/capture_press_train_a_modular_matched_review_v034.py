"""Non-overwriting correction to v033 review: preserve aimed camera roll except overhead."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_modular_matched_review_v033.py")
code = base.read_text(encoding="utf-8")
code = code.replace('OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/MatchedReview"', 'OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/MatchedReview_v034"')
code = code.replace("MATCHED_REVIEW_v033", "MATCHED_REVIEW_v034").replace("matched-review-v033", "matched-review-v034")
code = code.replace('f"train_a_matched_{name}_v033.png"', 'f"train_a_matched_{name}_v034.png"')
code = code.replace("for name, location, target, scale, roll in views:", "for name, location, target, scale, roll in views:")
code = code.replace("    cam.rotation_euler.z = roll\n", "    if name == \"top\":\n        cam.rotation_euler.z += roll\n")
code = code.replace("refusing to overwrite v033 matched review", "refusing to overwrite v034 matched review")
exec(compile(code, str(base) + "::v034", "exec"), globals(), globals())
