"""Create RP01 dock core v004 by closing the 10 mm anchor-plate over-width."""
from __future__ import annotations

import sys
from pathlib import Path

import bpy


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output .blend path required")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    root = bpy.data.objects["ROOT_LB_RP01_DOCK_CORE_V003"]
    root.name = "ROOT_LB_RP01_DOCK_CORE_V004"
    root["lb_status"] = "EXACT_OVERALL_WIDTH_SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_source_parent"] = "RP01_DOCK_CORE_V003"
    root["lb_authority_change"] = "NONE_DECORATIVE_ANCHOR_PLATE_WIDTH_CORRECTION_ONLY"

    changed = []
    for obj in bpy.data.objects:
        if obj.name.startswith("SM_LB_RP01_DockAnchorPlate_"):
            obj.dimensions.x = 0.180
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            obj.select_set(False)
            obj["lb_v004_reason"] = "CLOSE_5MM_PER_SIDE_NOMINAL_2600MM_ENVELOPE_EXCESS"
            changed.append(obj.name)
    if len(changed) != 4:
        raise RuntimeError(f"Expected four anchor plates, changed {len(changed)}")
    bpy.context.scene["lb_candidate"] = "RP01_DOCK_CORE_V004"
    bpy.context.scene["lb_promotion_authorized"] = False
    bpy.context.scene["lb_v004_changed_anchor_plates"] = changed
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved exact-overall-width shared core v004 {output}")


if __name__ == "__main__":
    main()
