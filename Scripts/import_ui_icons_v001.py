"""import_ui_icons_v001.py - UI icons into the game ("other games had
images of the parts" - owner, 2026-08-26). 19 model renders (stations,
drones, dock, both craft) + 37 item badges from
SourceAssets/.../Icons, imported as UI textures (sRGB, never stream,
UI group). Fail-closed: every listed icon must import."""

import os
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\StationModels_MeshyIntake_v001"
       r"\Icons")
DEST = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/UI"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
if not lib.does_directory_exist(DEST):
    lib.make_directory(DEST)
count = 0
failures = []
for fname in sorted(os.listdir(SRC)):
    if not fname.endswith(".png"):
        continue
    name = os.path.splitext(fname)[0]
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(SRC, fname), "destination_path": DEST,
        "destination_name": name, "automated": True,
        "replace_existing": True, "save": False})
    tools.import_asset_tasks([task])
    tex = unreal.load_asset("%s/%s" % (DEST, name))
    if tex is None:
        failures.append(name)
        continue
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("lod_group",
                            unreal.TextureGroup.TEXTUREGROUP_UI)
    lib.save_asset("%s/%s" % (DEST, name))
    count += 1
if failures:
    raise RuntimeError("FAIL CLOSED: icons failed: " + ", ".join(failures))
unreal.log("UI ICONS IMPORTED: %d" % count)
