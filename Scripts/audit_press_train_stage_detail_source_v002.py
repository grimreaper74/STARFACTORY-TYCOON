"""v002 source-audit adapter for corrected CCTV-facing stage detail."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_stage_detail_source_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("StageDetail_v001", "StageDetail_v002")
code = code.replace("stage-detail-v001", "stage-detail-v002")
code = code.replace("stage-detail-source-v001", "stage-detail-source-v002")
code = code.replace("_v001", "_v002")
code = code.replace("STAGE_DETAIL_V001", "STAGE_DETAIL_V002")
exec(compile(code, str(base) + "::stage_detail_v002", "exec"), globals(), globals())
