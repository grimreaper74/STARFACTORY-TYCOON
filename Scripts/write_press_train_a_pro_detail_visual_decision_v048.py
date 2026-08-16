"""Record the inspected v047 source decision; no asset mutation."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/CA_MW_PressTrainA_ProDetailModular_v046.blend"
FBX = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/FBX/SM_CA_MW_PressTrainA_ProDetailModular_v046.fbx"
REVIEW = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/MatchedReview_v047"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_pro_detail_source_decision_v048.json"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {OUT}")
captures = {}
for path in sorted(REVIEW.glob("*.png")):
    captures[path.name] = sha(path)
payload = {
    "$schema": "cairnwell/audit/press-train-a-pro-detail-source-decision-v048/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "RETAIN_SOURCE_DIRECTION__AUTHORIZE_ISOLATED_UNREAL_VISUAL_INTAKE_ONLY__NOT_REPLACEMENT_READY__NOT_PROMOTED",
    "source_blend_sha256": sha(SOURCE),
    "source_fbx_sha256": sha(FBX),
    "review_captures": captures,
    "inspected_findings": {
        "passes": [
            "S01 reads as a dedicated destack and blank-feed cell",
            "S02-S06 retain a coherent shared press-body family with station identities",
            "S04 and S05 service-side collection paths are visibly supported and connected",
            "S07 reads as a dedicated inspection/unload cell with articulated robot and HMI",
            "complete source remains within the existing 15 m protected train envelope",
        ],
        "open_release_holds": [
            "inherited-hall material and lighting comparison",
            "service-side access and bin-removal clearance",
            "separate visible mover asset mapping",
            "collision and navigation regression",
            "runtime, interlock, fault and save-authority regression",
            "final surface fabrication and station-specific cosmetic polish",
        ],
    },
    "isolated_unreal_visual_intake_authorized": True,
    "replacement_authorized": False,
    "runtime_authority_authorized": False,
    "collision_authorized": False,
    "navigation_authorized": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
