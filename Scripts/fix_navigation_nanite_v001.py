"""Disable Nanite on the Navigation asset, at the source, before any
presenter code ever touches it.

Navigation carries the canopy_glass slot, and this project has already
learned once (the spray booth) that Nanite cannot render translucency.
Fixed at the ASSET level rather than relying on every future spawn
site remembering to set bDisallowNanite on the component - that
precedent exists in the codebase but depends on someone remembering it
each time a mesh is instanced.
"""
import unreal

PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
        "Meshes/Scout01_v002/scout01_v002/StaticMeshes/Navigation"
        ".Navigation")
mesh = unreal.EditorAssetLibrary.load_asset(PATH)
if mesh is None:
    unreal.log_error("NAVFIX: asset not found at %s" % PATH)
else:
    settings = mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", settings)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.log("NAVFIX OK - Nanite disabled on Navigation (canopy_glass)")
