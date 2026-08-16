"""Record the independently inspected v028 fixed-camera crane visual gate."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = REPO / "Saved/ValidationScreenshots/PressShopIntegration/v028_pr004_crane_runtime"
OUT = REPO / "Saved/Audits/press_shop_pr004_crane_visual_gate_v028.json"
CAPTURES = {
    "full_span_runtime": "press_shop_v028_crane_full_span_runtime.png",
    "full_span_oblique_runtime": "press_shop_v028_crane_full_span_oblique_runtime.png",
    "c_hook_engagement_runtime": "press_shop_v028_c_hook_engagement_runtime.png",
    "pr004_deposit_runtime": "press_shop_v028_crane_deposit_runtime.png",
}


def png_size(path):
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Not a PNG: {path}")
    return struct.unpack(">II", header[16:24])


records = []
for capture_id, filename in CAPTURES.items():
    path = ROOT / filename
    if not path.is_file() or path.stat().st_size < 1024:
        raise RuntimeError(f"Missing fixed-camera evidence: {path}")
    width, height = png_size(path)
    records.append({
        "capture_id": capture_id,
        "path": str(path),
        "width": width,
        "height": height,
        "bytes": path.stat().st_size,
        "last_write_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "inspected": True,
    })

result = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-visual-gate-v028/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate": "PR-004 crane visual candidate v028",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028",
    "authoritative_references": [
        "Docs/References/PressShop_Revised_BareCoil_FrontEnd/v001/Sheet_1_Revised_Press_Shop_Master_Plan.png",
        "Docs/References/PressShop_Revised_BareCoil_FrontEnd/v001/Sheet_3_Revised_PR004_Cell.png",
        "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004A_Realistic_Robotic_Coil_Destrapping_Dewrapping_Cell_v002.jpg",
    ],
    "captures": records,
    "accepted_observations": {
        "40t_bridge_full_width": "PASS: two girders now span the measured 6210 cm between both runway end trucks.",
        "30t_bridge_full_width": "PASS: the secondary single-girder crane also uses the complete 6210 cm span.",
        "c_hook_engagement": "PASS FOR GEOMETRY: the padded lower arm is centred in the coil bore and remains 59 cm below the hook datum during travel.",
        "runtime_material_identity": "PASS: the packaged CS-10 coil and its Cairnwell identity attachments travel together and deposit as MCX-U-CS10-0001.",
        "pr004_deposit_readability": "PASS: the packaged coil, cradle, operator approach, touch HMI and nearby segregated bins are readable.",
    },
    "visual_blockers": [
        "The full-span bridge is now dimensionally correct, but repeated module capacity plates and clean joint rhythm still need a final fabrication pass with controlled splice hierarchy and a single readable crane identity plate.",
        "Crane steel remains too clean and bright versus the Pro factory references; edge wear, grease, trolley-rail contact, festoon cabling and maintenance detail are still absent.",
        "The packaged wrap is too smooth/bright and its travelling label loses contrast under the crane-path lighting; layered fibre, wrinkles, seams, tape and restrained dirt remain required.",
        "The span view proves width but a foreground structural column interrupts the centre; an unobstructed fixed management view is still required for promotion evidence.",
        "Ceiling and service-wall exposure remains uneven, with bright roof panels and black wall pockets below the release-quality lighting target.",
        "Only the 40 t PR-003/PR-004 crane has native transfer authority; the corrected 30 t PR-001/PR-002 crane is geometry-only and must receive its own later logistics authority.",
    ],
    "decision": {
        "visual_gate": "FAIL__REWORK_REQUIRED",
        "promotion": "FORBIDDEN",
        "runtime_gate": "PASS__NOT_PROMOTED",
        "next_priority": "Finish crane fabrication/material/lighting presentation and packaged-coil layering, then recapture unobstructed fixed views and rerun all gates.",
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"PR004_CRANE_V028_VISUAL_GATE_FAIL audit={OUT}")
