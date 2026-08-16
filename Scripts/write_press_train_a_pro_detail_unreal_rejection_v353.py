"""Record failed v353 axis intake without changing its partial map."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAProDetailVisualCandidate_v353.umap"
OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_pro_detail_visual_intake_rejection_v353.json"
if OUT.exists(): raise RuntimeError(f"Refusing to overwrite {OUT}")
payload={"$schema":"cairnwell/audit/press-train-a-pro-detail-visual-intake-rejection-v353/v1",
"generated_utc":datetime.now(timezone.utc).isoformat(),
"status":"REJECTED_TECHNICAL_PARTIAL__AXIS_GATE_FAILED__NEVER_PARENT_OR_PROMOTE",
"map_sha256":hashlib.sha256(MAP.read_bytes()).hexdigest().upper() if MAP.exists() else None,
"measured_candidate_world_size_cm":[939.0,5765.0,1356.5],
"diagnosis":"single-mesh geometry complete; inherited yaw maps FBX axes incorrectly",
"corrective_direction":"fresh v343 child with roll +90 degrees; no reuse of partial v353 map",
"protected_base_mutated":False,"parent_authorized":False,"promotion_authorized":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
print(json.dumps(payload,indent=2))
