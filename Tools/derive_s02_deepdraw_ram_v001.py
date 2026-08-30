"""Derive the animated S02 ram module without modifying the approved source.

The two meshes are exported together so the existing `PressRam_02` Unreal
component can keep its bounded Z motion while the authored ram and upper die
retain their exact source relationship.
"""

import hashlib
import json
import os

import bpy


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_BLEND = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_v001/CA_S02_DeepDraw_v001.blend"
SOURCE_FBX = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_v001/CA_S02_DeepDraw_v001.fbx"
OUTPUT_DIR = PROJECT_ROOT + "/ArtSource/Codex_S02_DeepDraw_Ram_v001"
OUTPUT_FBX = OUTPUT_DIR + "/CA_S02_DeepDraw_Ram_v001.fbx"
RECEIPT = OUTPUT_DIR + "/derivation_receipt.json"

ROOT_NAME = "SM_CA_MW_PTA_S02_PressRoot"
RAM_NAMES = [
    "SM_CA_MW_PTA_S02_RamMover",
    "SM_CA_MW_PTA_S02_DieUpper",
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def fail(message):
    raise RuntimeError("S02 ram derivation failed: {}".format(message))


if not os.path.isfile(SOURCE_BLEND):
    fail("source blend is missing: {}".format(SOURCE_BLEND))
if not os.path.isfile(SOURCE_FBX):
    fail("source FBX is missing: {}".format(SOURCE_FBX))
if os.path.exists(OUTPUT_FBX) or os.path.exists(RECEIPT):
    fail("output already exists; overwrite is forbidden: {}".format(OUTPUT_DIR))

root = bpy.data.objects.get(ROOT_NAME)
if root is None:
    fail("source root is missing: {}".format(ROOT_NAME))

ram_meshes = []
for name in RAM_NAMES:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        fail("expected mesh is missing: {}".format(name))
    current = obj
    is_under_root = False
    while current is not None:
        if current == root:
            is_under_root = True
            break
        current = current.parent
    if not is_under_root:
        fail("expected mesh is not under press root: {}".format(name))
    ram_meshes.append(obj)

if ram_meshes[1].parent != ram_meshes[0]:
    fail("upper die is not parented to the ram mover")

os.makedirs(OUTPUT_DIR, exist_ok=False)

bpy.ops.object.select_all(action="DESELECT")
for obj in ram_meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ram_meshes[0]

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
    fail("ram FBX was not written")

receipt = {
    "schema": "lineboss/onefactory/press/s02-deepdraw-ram-derivation/v1",
    "status": "PASS__RAM_MODULE_DERIVED_WITHOUT_SOURCE_OVERWRITE",
    "source_blend": SOURCE_BLEND,
    "source_fbx": SOURCE_FBX,
    "source_fbx_sha256": sha256(SOURCE_FBX),
    "output_fbx": OUTPUT_FBX,
    "output_fbx_sha256": sha256(OUTPUT_FBX),
    "root": ROOT_NAME,
    "exported_meshes": RAM_NAMES,
    "upper_die_parent": ram_meshes[1].parent.name,
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

print("LINE_BOSS_S02_RAM_DERIVATION=" + json.dumps(receipt, sort_keys=True))
