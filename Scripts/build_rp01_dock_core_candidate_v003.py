"""Create RP01 dock core v003 by clearing the MR01 rack service aperture.

Run with the retained v002 core open. The shared diagnostics/HMI station is
post-mounted on the outer right front upright; exact base and charging/network
sockets are not changed.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output .blend path required")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    root = bpy.data.objects["ROOT_LB_RP01_DOCK_CORE_V002"]
    root.name = "ROOT_LB_RP01_DOCK_CORE_V003"
    root["lb_status"] = "SERVICE_APERTURE_SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_source_parent"] = "RP01_DOCK_CORE_V002"
    root["lb_authority_change"] = "NONE_PRESENTATION_PACKAGING_ONLY"

    # The v002 front-facing controls sat directly in the authorized MR01 rack
    # access corridor. Turn them onto the outer face of the right-front post.
    # All resulting geometry remains within the retained +/-1300 mm dock width.
    placements = {
        "SM_LB_RP01_DockDiagnosticsPanel": (1.245, 0.97, 0.65),
        "SM_LB_RP01_DockServiceHMI": (1.272, 0.97, 1.01),
    }
    for name, location in placements.items():
        obj = bpy.data.objects[name]
        obj.location = location
        obj.rotation_euler.z += math.radians(90.0)
        obj["lb_v003_reason"] = "POST_MOUNTED_TO_CLEAR_MR01_TOOL_RACK_ACCESS"

    estop = bpy.data.objects["SM_LB_RP01_DockEStop"]
    estop.location = (1.245, 0.78, 0.76)
    estop["lb_v003_reason"] = "RETAINED_ACCESSIBLE_OUTER_POST_POSITION"

    bpy.context.scene["lb_candidate"] = "RP01_DOCK_CORE_V003"
    bpy.context.scene["lb_promotion_authorized"] = False
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved service-aperture shared core v003 {output}")


if __name__ == "__main__":
    main()
