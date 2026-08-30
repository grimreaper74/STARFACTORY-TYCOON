"""enable_nanite_v001.py - flags Nanite on the imported spacecraft-era
static meshes (owner 2026-08-26 night: "how do you get full detail,
lights, shadows"). Nanite is project-enabled but per-mesh OFF for every
lane import so far; this pass enables it on the LOD0 masters (Nanite
supersedes the LOD chain; the LOD1 assets stay as evidence and for any
non-Nanite platform fallback). The translucent canopy glass meshes are
SKIPPED - translucency does not run through Nanite. Logs every change;
fails closed if a listed root is missing."""

import unreal

lib = unreal.EditorAssetLibrary

ROOTS = [
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Drones",
    "/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001/Meshes",
]
SKIP_SUBSTRINGS = ("Canopy",)   # translucent glass stays non-Nanite

changed = 0
skipped = 0
for root in ROOTS:
    if not lib.does_directory_exist(root):
        raise RuntimeError("FAIL CLOSED: missing root " + root)
    for asset_path in lib.list_assets(root, recursive=True):
        name = asset_path.split("/")[-1].split(".")[0]
        if not name.startswith("SM_"):
            continue
        if any(s in name for s in SKIP_SUBSTRINGS):
            skipped += 1
            continue
        mesh = unreal.load_asset(asset_path)
        if mesh is None or not isinstance(mesh, unreal.StaticMesh):
            continue
        nanite = mesh.get_editor_property("nanite_settings")
        if nanite.get_editor_property("enabled"):
            continue
        nanite.set_editor_property("enabled", True)
        # The subsystem call rebuilds the Nanite data, not just the flag.
        sm_subsystem = unreal.get_editor_subsystem(
            unreal.StaticMeshEditorSubsystem)
        sm_subsystem.set_nanite_settings(mesh, nanite, True)
        lib.save_asset(asset_path.split(".")[0])
        changed += 1
        unreal.log("NANITE ENABLED " + name)
unreal.log("NANITE PASS DONE: %d enabled, %d glass skipped"
           % (changed, skipped))
