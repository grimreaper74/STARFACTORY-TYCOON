"""Import the generated hall shell into the interior folder.

Runs INSIDE the editor (-ExecutePythonScript). Follows the parts lane:
declare a triangle budget per mesh, import, then MEASURE and report,
because a generated asset's record is a pinned source, a hash, a
declared budget and a measurement - not its birthplace.

INTERCHANGE NESTS EACH IMPORT in its own <Name>/StaticMeshes/ folder
rather than laying them flat beside their siblings, so the loader in
LBSpacecraftWIPPresentationActor must use the nested path. A flat path
returns null, and a null mesh here draws nothing at all - the hall
would simply have no walls again, silently.
"""
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Spacecraft\HallInterior_v001")
DEST = "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001"

# Declared budgets. These are simple extruded box assemblies; anything
# far above this means the generator changed and nobody noticed.
BUDGET = {
    "SM_LB_IN_WallBay": 400,
    "SM_LB_IN_RoofTruss": 900,
    "SM_LB_IN_BayLight": 300,
}

tools = unreal.AssetToolsHelpers.get_asset_tools()
registry = unreal.AssetRegistryHelpers.get_asset_registry()
problems = []

for name in sorted(BUDGET):
    path = "%s\\%s.glb" % (SRC, name)
    if not unreal.Paths.file_exists(path):
        problems.append("%s: SOURCE MISSING %s" % (name, path))
        continue
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = DEST
    task.automated = True
    task.replace_existing = True
    task.save = True
    tools.import_asset_tasks([task])

meshes = {}
for data in registry.get_assets_by_path(DEST, recursive=True):
    asset = data.get_asset()
    if isinstance(asset, unreal.StaticMesh):
        meshes[asset.get_name()] = asset

for name, declared in sorted(BUDGET.items()):
    mesh = next((m for k, m in meshes.items() if k.startswith(name)), None)
    if mesh is None:
        problems.append("%s: NOT IMPORTED" % name)
        continue
    actual = mesh.get_num_triangles(0)
    b = mesh.get_bounds().box_extent
    unreal.log("HALL %s tris=%d (budget %d) extent=%.0f x %.0f x %.0f cm"
               % (name, actual, declared, b.x * 2, b.y * 2, b.z * 2))
    if actual > declared:
        problems.append("%s: %d tris over declared %d"
                        % (name, actual, declared))

if problems:
    for p in problems:
        unreal.log_error("HALL IMPORT PROBLEM: %s" % p)
    unreal.log_error("HALL IMPORT FAILED")
else:
    unreal.log("HALL IMPORT OK - %d meshes" % len(BUDGET))
