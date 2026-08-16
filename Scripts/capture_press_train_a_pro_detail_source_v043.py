"""Fresh matched Blender review of Pro-detail source v042."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_modular_matched_review_v033.py")
code = base.read_text(encoding="utf-8")
code = code.replace("ModularAssembly_v033/CA_MW_PressTrainA_ModularAssembly_v033.blend",
                    "ProDetailModular_v042/CA_MW_PressTrainA_ProDetailModular_v042.blend")
code = code.replace('OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/MatchedReview"',
                    'OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v042/MatchedReview_v043"')
code = code.replace("MATCHED_REVIEW_v033", "PRO_DETAIL_MATCHED_REVIEW_v043")
code = code.replace("matched-review-v033", "pro-detail-matched-review-v043")
code = code.replace('f"train_a_matched_{name}_v033.png"', 'f"train_a_pro_detail_{name}_v043.png"')
code = code.replace("    cam.rotation_euler.z = roll\n", "    if name == \"top\":\n        cam.rotation_euler.z += roll\n")
code = code.replace("refusing to overwrite v033 matched review", "refusing to overwrite v043 Pro-detail review")
code = code.replace('("operator", (72, 22.5, 5.7), (0, 22.5, 4.4), 52, 0)',
                    '("operator", (78, 23.5, 6.8), (0, 23.5, 4.2), 60, 0)')
code = code.replace('("rear", (-72, 22.5, 5.7), (0, 22.5, 4.4), 52, 0)',
                    '("rear", (-78, 23.5, 6.8), (0, 23.5, 4.2), 60, 0)')
code = code.replace('("elevated", (55, -18, 34), (0, 22.5, 3.3), 60, 0)',
                    '("elevated", (62, -22, 38), (0, 23.5, 3.6), 68, 0)')
code = code.replace('("top", (0, 22.5, 90), (0, 22.5, 0), 52, math.pi / 2)',
                    '("top", (0, 23.5, 95), (0, 23.5, 0), 60, math.pi / 2)')
exec(compile(code, str(base) + "::v043", "exec"), globals(), globals())
