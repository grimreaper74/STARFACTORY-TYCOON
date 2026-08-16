"""Record the failed dimensional intake without altering its partial artifact."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAProDetailVisualCandidate_v351.umap"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_pro_detail_visual_intake_rejection_v351.json"
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {OUT}")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
payload = {"$schema": "cairnwell/audit/press-train-a-pro-detail-visual-intake-rejection-v351/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "REJECTED_TECHNICAL_PARTIAL__DIMENSION_GATE_FAILED__NEVER_PARENT_OR_PROMOTE",
    "map_sha256": sha(MAP) if MAP.exists() else None,
    "measured_candidate_world_size_cm": [1344.0, 4800.0, 1045.75],
    "failed_expectation": "Imported combined asset did not preserve the source-reviewed longitudinal envelope",
    "protected_base_mutated": False, "parent_authorized": False, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
