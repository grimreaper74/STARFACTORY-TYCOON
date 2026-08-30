"""Derive a static S02 shell FBX from the approved Blender source without modifying it.

The existing Unreal train already owns the S02 ram motion. This pass therefore
exports every visible source mesh except the authored moving ram and upper die.
It gives the runtime integration a non-duplicating shell while preserving the
working `PressRam_02` animation seam. The source .blend is opened read-only in
practice: this script never saves it and writes only a new, namespaced source
derivative plus a transparent receipt.
"""

import hashlib
import json
import os

import bpy


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_BLEND = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_v001/CA_S02_DeepDraw_v001.blend"
SOURCE_FBX = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_v001/CA_S02_DeepDraw_v001.fbx"
OUTPUT_DIR = PROJECT_ROOT + "/ArtSource/Codex_S02_DeepDraw_Static_v001"
OUTPUT_FBX = OUTPUT_DIR + "/CA_S02_DeepDraw_Static_v001.fbx"
RECEIPT = OUTPUT_DIR + "/derivation_receipt.json"

ROOT_NAME = "SM_CA_MW_PTA_S02_PressRoot"
MOVING_NAMES = {
    "SM_CA_MW_PTA_S02_RamMover",
    "SM_CA_MW_PTA_S02_DieUpper",
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def fail(message):
    raise RuntimeError("S02 static derivation failed: {}".format(message))


def is_under_root(obj, root):
    current = obj
    while current is not None:
        if current == root:
            return True
        current = current.parent
    return False


if not os.path.isfile(SOURCE_BLEND):
    fail("source blend is missing: {}".format(SOURCE_BLEND))
if not os.path.isfile(SOURCE_FBX):
    fail("source FBX is missing: {}".format(SOURCE_FBX))
if os.path.exists(OUTPUT_FBX) or os.path.exists(RECEIPT):
    fail("output already exists; overwrite is forbidden: {}".format(OUTPUT_DIR))

root = bpy.data.objects.get(ROOT_NAME)
if root is None:
    fail("source root is missing: {}".format(ROOT_NAME))

source_meshes = sorted(
    [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and is_under_root(obj, root)
    ],
    key=lambda obj: obj.name,
)
if not source_meshes:
    fail("no source meshes were found under the press root")

by_name = {obj.name: obj for obj in source_meshes}
missing_movers = sorted(MOVING_NAMES.difference(by_name))
if missing_movers:
    fail("expected moving source meshes are missing: {}".format(missing_movers))

static_meshes = [obj for obj in source_meshes if obj.name not in MOVING_NAMES]
if len(static_meshes) >= len(source_meshes):
    fail("moving meshes were not excluded")

os.makedirs(OUTPUT_DIR, exist_ok=False)

bpy.ops.object.select_all(action="DESELECT")
for obj in static_meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = static_meshes[0]

bpy.ops.export_scene.fbx(
    filepath=OUTPUT_FBX,
    use_selection=True,
    use_active_collection=False,
    object_types={"MESH"},
    use_mesh_modifiers=True,
    mesh_smooth_type="FACE",
    add_leaf_bones=False,
    bake_anim=False,
    apply_scale_options="FBX_SCALE_NONE",
)

if not os.path.isfile(OUTPUT_FBX) or os.path.getsize(OUTPUT_FBX) == 0:
    fail("static FBX was not written")

receipt = {
    "schema": "lineboss/onefactory/press/s02-deepdraw-static-derivation/v1",
    "status": "PASS__STATIC_SHELL_DERIVED_WITHOUT_SOURCE_OVERWRITE",
    "source_blend": SOURCE_BLEND,
    "source_fbx": SOURCE_FBX,
    "source_fbx_sha256": sha256(SOURCE_FBX),
    "output_fbx": OUTPUT_FBX,
    "output_fbx_sha256": sha256(OUTPUT_FBX),
    "root": ROOT_NAME,
    "source_mesh_count": len(source_meshes),
    "static_mesh_count": len(static_meshes),
    "excluded_moving_meshes": sorted(MOVING_NAMES),
    "exported_meshes": [obj.name for obj in static_meshes],
    "fbx_export": {
        "use_selection": True,
        "combine_in_unreal": True,
        "apply_scale_options": "FBX_SCALE_NONE",
        "bake_anim": False,
    },
}
with open(RECEIPT, "w", encoding="utf-8") as handle:
    json.dump(receipt, handle, indent=2, sort_keys=True)
    handle.write("\n")

print("LINE_BOSS_S02_STATIC_DERIVATION=" + json.dumps(receipt, sort_keys=True))
