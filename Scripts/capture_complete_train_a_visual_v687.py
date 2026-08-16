"""Capture v686 Train A review map with visible floor."""
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir())
source_path = project / r"Scripts\capture_complete_train_a_visual_v683.py"
source = source_path.read_text(encoding="utf-8")
source = source.replace(
    "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReview_v682",
    "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReviewFloor_v686")
source = source.replace("_v682", "_v686").replace("_V682", "_V686")
source = source.replace("v683", "v687").replace("V683", "V687")
exec(compile(source, str(source_path), "exec"), globals(), globals())
