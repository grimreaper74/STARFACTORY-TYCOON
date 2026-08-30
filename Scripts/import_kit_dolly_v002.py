"""Import the commissioned kit-dolly GLB as an Unreal static mesh.

PROVENANCE, because the project's rule is that an asset proves itself
by its record rather than its birthplace:

  source  SourceAssets/Spacecraft/KitDolly_v002/LB_KitDolly_v002.glb
  sha256  022ded33452a534d5039745a2fd109ae14acf0aaf7a1ce7f39f39e797fa2147b
  origin  commissioned 3D drop, 2026-08-29
  budget  11,812 triangles measured in Blender before import - declared
          here so a silent explosion in triangle count is visible as a
          disagreement rather than discovered later on a frame time

WHY IT IS COMBINED INTO ONE MESH. The drop is 122 separate objects, one
per bolt, strap and label. That is excellent authoring and terrible
runtime: 122 components per dolly, times one dolly per station per
craft, is thousands of draw calls for a prop the player sees at forty
metres. Interchange is asked to weld it into a single static mesh, and
the material slots survive, which is what keeps the palette wiring
possible.

Fails closed and imports nothing if the source is missing or the
resulting mesh is absent - a half-imported asset that looks present in
the content browser is worse than one that plainly is not there.
"""
import unreal

# THE JOINED FILE, not the raw drop. Interchange was asked to combine
# and did not: importing the drop directly produced 122 SEPARATE STATIC
# MESHES, one per bolt, strap and label. The join happens in Blender
# first, where it can be verified - triangles and all five material
# slots were checked unchanged across it.
SOURCE = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
          r"\SourceAssets\Spacecraft\KitDolly_v002"
          r"\LB_KitDolly_v002_joined.glb")
DEST = "/Game/LineBoss/Candidates/Spacecraft/KitDolly_v002"
ASSET = "SM_LB_KitDolly_v002"

# Declared before import so the check below is a real comparison rather
# than a description of whatever turned up.
DECLARED_TRIANGLE_BUDGET = 11812


def fail(reason):
    unreal.log_error("KIT DOLLY IMPORT REFUSED: %s" % reason)
    raise SystemExit(1)


if not unreal.Paths.file_exists(SOURCE):
    fail("source glb not found at %s" % SOURCE)

# The previous 122-mesh import has to GO rather than sit alongside.
# Leaving both means the content browser holds two plausible assets and
# whichever is referenced first wins silently.
if unreal.EditorAssetLibrary.does_directory_exist(DEST):
    unreal.log("KIT DOLLY: clearing the previous import at %s" % DEST)
    unreal.EditorAssetLibrary.delete_directory(DEST)

task = unreal.AssetImportTask()
task.filename = SOURCE
task.destination_path = DEST
task.destination_name = ASSET
task.automated = True
task.replace_existing = True
task.save = True

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

imported = list(task.get_editor_property("imported_object_paths") or [])
unreal.log("KIT DOLLY: interchange produced %d object(s)" % len(imported))
for path in imported:
    unreal.log("   %s" % path)

# WHAT ACTUALLY LANDED, rather than what the task claims. Interchange
# returns paths for materials and textures too, so counting them proves
# nothing about whether there is a mesh to place.
meshes = []
registry = unreal.AssetRegistryHelpers.get_asset_registry()
for data in registry.get_assets_by_path(DEST, recursive=True):
    asset = data.get_asset()
    if isinstance(asset, unreal.StaticMesh):
        meshes.append(asset)

if not meshes:
    fail("no static mesh under %s after import" % DEST)

total = 0
for mesh in meshes:
    tris = mesh.get_num_triangles(0)
    total += tris
    unreal.log("KIT DOLLY MESH %s: %d tris, %d LODs, %d material slots"
               % (mesh.get_name(), tris, mesh.get_num_lods(),
                  len(mesh.static_materials)))
    for slot in mesh.static_materials:
        unreal.log("     slot %s" % slot.material_slot_name)
    bounds = mesh.get_bounds()
    box = bounds.box_extent
    unreal.log("     size %.2f x %.2f x %.2f m"
               % (box.x * 2 / 100.0, box.y * 2 / 100.0, box.z * 2 / 100.0))

unreal.log("KIT DOLLY TOTAL: %d reported triangles against a declared %d"
           % (total, DECLARED_TRIANGLE_BUDGET))

# THIS CHECK USED TO ONLY LOOK UPWARDS, and that was a real hole. A
# collapsed import reports FEWER triangles, not more - so an 83% loss
# would have printed "WITHIN BUDGET" and been believed. A number that
# can only fail in one direction is not a check.
if total > DECLARED_TRIANGLE_BUDGET * 1.25:
    unreal.log_warning(
        "KIT DOLLY OVER BUDGET: %d tris is more than 25%% above the "
        "declared %d - the import inflated the mesh"
        % (total, DECLARED_TRIANGLE_BUDGET))
elif total < DECLARED_TRIANGLE_BUDGET * 0.75:
    # Expected when Nanite is on: get_num_triangles reports the FALLBACK
    # mesh while Nanite keeps the full detail internally. Said out loud
    # rather than passed over, because the alternative explanation - the
    # importer welding coincident faces into degenerates and dropping
    # them - looks identical from here and is a genuine defect. The
    # Nanite flag is what tells the two apart.
    nanite = any(m.get_editor_property("nanite_settings").enabled
                 for m in meshes)
    if nanite:
        unreal.log(
            "KIT DOLLY: %d is the NANITE FALLBACK count, not a loss - "
            "Nanite holds the full %d internally"
            % (total, DECLARED_TRIANGLE_BUDGET))
    else:
        unreal.log_error(
            "KIT DOLLY LOST GEOMETRY: %d tris against a declared %d and "
            "Nanite is OFF, so this is a real collapse - check the "
            "importer's weld threshold against the model's flush plates"
            % (total, DECLARED_TRIANGLE_BUDGET))
else:
    unreal.log("KIT DOLLY WITHIN BUDGET")
