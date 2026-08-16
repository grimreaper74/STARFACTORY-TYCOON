"""Export the retained MR01 v022 static payload with native CFR X-forward FBX axes.

The exact object allow-list is derived from the already-gated v020 payload asset
names.  This keeps evidence-only, socket, validation and linked RP01 objects out of
the new import while carrying the v022 side-bumper correction forward.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import bpy


PROJECT = Path(__file__).resolve().parents[1]
V020_PAYLOAD = PROJECT / "Content/LineBoss/Robots/Maintenance/MR01/Candidate_v020/Payload"
EXPORT_DIR = PROJECT / "SourceAssets/Robots/LB_MR01_MaintenanceRobot/Exports/Candidate_v022_IsolatedImport"
FBX = EXPORT_DIR / "LB_MR01_StaticPayload_v022.fbx"
AUDIT = PROJECT / "Saved/Audits/SupportRobots/mr01_v022_static_payload_export.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


asset_names = {
    path.stem
    for path in V020_PAYLOAD.glob("*.uasset")
    if not path.stem.startswith("M_")
}
if len(asset_names) != 345:
    raise RuntimeError("Expected 345 retained payload mesh names, found {}".format(len(asset_names)))

selected = []
missing = []
bpy.ops.object.select_all(action="DESELECT")
for name in sorted(asset_names):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        missing.append(name)
        continue
    obj.hide_set(False)
    obj.select_set(True)
    selected.append(obj)

if missing or len(selected) != 345:
    raise RuntimeError("v022 payload selection mismatch: selected={}, missing={}".format(len(selected), missing))

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
bpy.context.view_layer.objects.active = selected[0]
bpy.ops.export_scene.fbx(
    filepath=str(FBX),
    use_selection=True,
    object_types={"MESH"},
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL",
    axis_forward="-Y",
    axis_up="Z",
    use_mesh_modifiers=True,
    use_custom_props=True,
    add_leaf_bones=False,
    bake_anim=False,
)

payload = {
    "$schema": "cairnwell/audit/mr01-v022-static-payload-export/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RETAINED_V022_STATIC_PAYLOAD_EXPORTED__UNREAL_INTAKE_OPEN__NOT_PROMOTED",
    "source_blend": bpy.data.filepath,
    "source_blend_sha256": sha256(Path(bpy.data.filepath)),
    "selection_authority": str(V020_PAYLOAD),
    "selected_mesh_count": len(selected),
    "selected_names": sorted(obj.name for obj in selected),
    "fbx": str(FBX),
    "fbx_sha256": sha256(FBX),
    "fbx_axes": {"forward": "-Y", "up": "Z", "interpretation": "Blender -Y = CFR +X"},
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print("LINE_BOSS_MR01_V022_PAYLOAD_EXPORT {}".format(payload["status"]))
