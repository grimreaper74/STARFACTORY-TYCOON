"""Record the independently inspected PR-004 fixed-camera visual gate."""

from __future__ import annotations

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = REPO / "Saved/ValidationScreenshots/PR004/Candidate_v002"
OUT = REPO / "Saved/Audits/pr004_fixed_camera_visual_gate_v004.json"

CAPTURES = {
    "overview_sw": "pr004_candidate_v002_overview_sw_final.png",
    "overview_ne": "pr004_candidate_v002_overview_ne_final.png",
    "top": "pr004_candidate_v002_top_final.png",
    "cradle_close": "pr004_candidate_v002_cradle_close_final.png",
    "robot_tools": "pr004_candidate_v002_robot_tools_final.png",
    "packaging_close": "pr004_candidate_v002_packaging_close_final.png",
    "film_dewrap": "pr004_candidate_v002_film_dewrap_final.png",
}


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


records = []
for capture_id, filename in CAPTURES.items():
    path = ROOT / filename
    if not path.is_file():
        raise RuntimeError(f"Missing required fixed-camera evidence: {path}")
    width, height = png_size(path)
    records.append({
        "capture_id": capture_id,
        "path": str(path),
        "width": width,
        "height": height,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "inspected": True,
    })

result = {
    "$schema": "line-boss/audit/pr004-fixed-camera-visual-gate/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate": "PR004 Candidate_v002 with validation lighting v004",
    "map": "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002",
    "reference_sheets": [
        "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004A_Realistic_Robotic_Coil_Destrapping_Dewrapping_Cell_v002.jpg",
        "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004_Powered_Coil_Wrap_Dewinding_Compaction_Module_RevA.jpg",
    ],
    "capture_method": "Unreal AutomationLibrary.take_high_res_screenshot through fixed CameraActor; direct SceneCapture2D rejected after PR005 A/B showed false monochrome output",
    "captures": records,
    "technical_observations": {
        "colour_capture": "PASS",
        "fixed_camera_files": "PASS",
        "flat_ended_coil_readability": "PASS",
        "fence_posts_and_mesh_readability": "PASS",
        "locked_cell_envelope_readability": "PASS",
    },
    "visual_blockers": [
        "Materials are flat category colours and lack the close-range PBR variation shown by the Pro references and Blender source renders.",
        "Packaged coil wrap is too smooth and uniform; seams, fibre mottling, restrained wrinkles, tape, readable identity label and credible edge-protector construction need release treatment.",
        "Robot/tool-change close camera currently frames an unfinished black housing and blue cylinder rather than the four recognisable guarded tool modules.",
        "Film dewrapping module reads as a black box; tab clamp, powered spindle, dancer, nip rollers, transfer path and compactor discharge are not visually self-explanatory.",
        "Cell lacks finished operator HMI, labelled waste segregation, inspection towers and maintenance/safety dressing visible in the authoritative sheets.",
        "Lighting is suitable for inspection but still validation-only and not production factory lighting.",
        "No fresh animation proof exists for indexing cradle, band capture/winding, dewrap tension path, compaction or waste ejection.",
        "Release collision, interaction and runtime controller binding remain unproven.",
    ],
    "decision": {
        "visual_gate": "FAIL",
        "promotion": "FORBIDDEN",
        "next_asset_priority": "Rebuild packaged-coil/cradle presentation as the first release-material candidate, then correct tool rack and film process readability.",
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"PR004_FIXED_CAMERA_VISUAL_GATE_FAIL audit={OUT}")
