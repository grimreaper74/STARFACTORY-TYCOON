"""Fresh matched Blender review of connected Pro-detail source v046."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_pro_detail_source_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace("ProDetailModular_v042/CA_MW_PressTrainA_ProDetailModular_v042.blend",
                    "ProDetailModular_v046/CA_MW_PressTrainA_ProDetailModular_v046.blend")
code = code.replace("ProDetailModular_v042/MatchedReview_v043", "ProDetailModular_v046/MatchedReview_v047")
code = code.replace("PRO_DETAIL_MATCHED_REVIEW_v043", "PRO_DETAIL_MATCHED_REVIEW_v047")
code = code.replace("pro-detail-matched-review-v043", "pro-detail-matched-review-v047")
code = code.replace("train_a_pro_detail_{name}_v043.png", "train_a_pro_detail_{name}_v047.png")
code = code.replace("v043 Pro-detail review", "v047 Pro-detail review")
exec(compile(code, str(base) + "::v047", "exec"), globals(), globals())
