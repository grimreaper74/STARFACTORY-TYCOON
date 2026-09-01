"""Diagnostic: engine BasicShapeMaterial onto line_station_v001 slots."""
import unreal
mesh = unreal.load_asset("/Game/Spacecraft/Props/line_station_v001/line_station_v001")
mat = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
mats = mesh.get_editor_property("static_materials")
for i in range(len(mats)):
    mesh.set_material(i, mat)
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
unreal.log("SWAPPED %d slots to BasicShapeMaterial" % len(mats))
