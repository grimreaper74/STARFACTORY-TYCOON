"""Build CR01 dock v005 on the linked RP01 robot-centred shared dock core."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import bpy


EXPECTED_V004_SHA256 = "2FD9789F8352C763F3EB4EB779C176BC9B06D0A56E87A22E221ADEDF1E430C90"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- shared_core.blend output_v005.blend")
    shared_path = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    source = Path(bpy.data.filepath).resolve()
    if sha256(source) != EXPECTED_V004_SHA256:
        raise RuntimeError("Refusing to build CR01 v005 from an unexpected v004 source")

    root = bpy.data.objects.get("ROOT_LB_CR01_SERVICE_DOCK")
    if not root:
        raise RuntimeError("Missing CR01 v004 root")

    # Remove only the superseded local copies of the old common dock. The
    # cleaning-specific wet-service geometry remains intact and is translated
    # into the shared robot-centred CFR below.
    for collection_name in ("10_LB_RP01_DOCK_SHARED_STATIC", "11_LB_RP01_DOCK_SHARED_MOVING"):
        collection = bpy.data.collections.get(collection_name)
        if collection:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
    for name in (
        "SCK_DockDatum", "SCK_ChargeContact_L", "SCK_ChargeContact_R", "SCK_NetworkContact",
        "UCX_SM_LB_RP01_DockBackPanel_00", "UCX_SM_LB_RP01_DockBase_00", "REF_LB_CR01_DockEnvelope",
    ):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    # v004's standalone origin is 1,445 mm in front of the docked CR01 centre.
    # Translate cleaning-only content into the same robot-centred CFR used by
    # MR01 and the new RP01 shared core. Old Blender Y -710 becomes +735 mm.
    shifted = []
    for collection_name in ("20_LB_CR01_DOCK_STATIC", "21_LB_CR01_DOCK_MOVING"):
        collection = bpy.data.collections.get(collection_name)
        if not collection:
            raise RuntimeError(f"Missing cleaning collection {collection_name}")
        for obj in collection.objects:
            obj.location.y += 1.445
            obj["lb_v005_robot_centred_shift_mm"] = 1445.0
            shifted.append(obj.name)
    for name in ("SCK_WaterFill", "SCK_DirtyExtract"):
        obj = bpy.data.objects.get(name)
        if not obj:
            raise RuntimeError(f"Missing cleaning socket {name}")
        obj.location.y += 1.445
        obj["lb_v005_robot_centred_shift_mm"] = 1445.0
        shifted.append(obj.name)

    with bpy.data.libraries.load(str(shared_path), link=True) as (source_data, target):
        required = ["LB_RP01_DOCK_SHARED", "LB_RP01_DOCK_SOCKETS"]
        missing = [name for name in required if name not in source_data.collections]
        if missing:
            raise RuntimeError(f"Shared dock collections missing: {missing}")
        target.collections = required
    for linked_collection in target.collections:
        bpy.context.scene.collection.children.link(linked_collection)
    bpy.context.view_layer.update()

    root.name = "ROOT_LB_CR01_SERVICE_DOCK_V005"
    root["lb_candidate"] = "LB_CR01_Dock_Candidate_v005"
    root["lb_status"] = "SOURCE_CANDIDATE_NOT_PROMOTED"
    root["lb_shared_library"] = str(shared_path)
    root["lb_coordinate_convention"] = "DOCKED_ROBOT_CFR"
    root["lb_cr01_outside_envelope"] = "TBC_CONFLICTING_REFERENCE_VALUES_NOT_INVENTED"
    root["lb_shifted_cleaning_object_count"] = len(shifted)
    scene = bpy.context.scene
    scene["lb_candidate"] = "LB_CR01_Dock_Candidate_v005"
    scene["lb_status"] = "SOURCE_CANDIDATE_NOT_PROMOTED"
    scene["lb_promotion_authorized"] = False
    scene["lb_source_v004_sha256"] = EXPECTED_V004_SHA256

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"Saved {output}; shifted {len(shifted)} cleaning-only objects into robot-centred CFR")


if __name__ == "__main__":
    main()
