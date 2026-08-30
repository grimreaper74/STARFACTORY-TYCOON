"""Import the six-assembly Scout-01 v002 craft and report exactly what
landed, at every path, with every triangle count and material slot.

The project has hit "asset unavailable, falling back to a placeholder"
three separate times this week from a guessed import path, because
Interchange nests each object in its own <Name>/StaticMeshes/ folder
and does not honour multi-object combine requests. This does not
guess: it imports, then WALKS the destination directory and prints
what is actually there, so the presenter code is written against
truth rather than an assumed convention.
"""
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Spacecraft\Scout01_v002\scout01_v002.glb")
DEST = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/Meshes/Scout01_v002"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
if unreal.EditorAssetLibrary.does_directory_exist(DEST):
    unreal.log("SCOUTV2: clearing previous import at %s" % DEST)
    unreal.EditorAssetLibrary.delete_directory(DEST)

task = unreal.AssetImportTask()
task.filename = SRC
task.destination_path = DEST
task.automated = True
task.replace_existing = True
task.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

EXPECT = {"Hull", "Propulsion", "Power", "Electronics", "Navigation",
          "Interior"}
found = {}
for data in registry.get_assets_by_path(DEST, recursive=True):
    asset = data.get_asset()
    if not isinstance(asset, unreal.StaticMesh):
        continue
    name = asset.get_name()
    path = asset.get_path_name()
    tris = asset.get_num_triangles(0)
    nanite = asset.get_editor_property("nanite_settings").enabled
    mats = []
    for slot in asset.get_editor_property("static_materials"):
        mi = slot.get_editor_property("material_interface")
        mats.append(str(slot.get_editor_property("material_slot_name")))
    unreal.log("SCOUTV2 ASSET %-16s tris=%-7d nanite=%-5s mats=%s  path=%s"
               % (name, tris, nanite, mats, path))
    for part in EXPECT:
        if name.startswith(part):
            found[part] = path

missing = EXPECT - set(found)
if missing:
    for m in sorted(missing):
        unreal.log_error("SCOUTV2 MISSING PART: %s" % m)
    unreal.log_error("SCOUTV2 IMPORT INCOMPLETE")
else:
    unreal.log("SCOUTV2 IMPORT OK - all six parts present")
    for part in sorted(found):
        unreal.log("SCOUTV2 PATH %s = %s" % (part, found[part]))
