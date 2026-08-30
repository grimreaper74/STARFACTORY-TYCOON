"""Check what is ACTUALLY imported right now for every entry gated
today, not what the folder-name pattern implied. The paint booth
proved the pattern-match was wrong at least once - this checks the
rest rather than assume they are fine or assume they are all wrong.
"""
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()

CHECK = [
    ("LiftCradle stage 1",
     "/Game/LineBoss/Candidates/Spacecraft/LiftCradle_v001/"
     "LB_Lift_lift_stage_1/StaticMeshes/LB_Lift_lift_stage_1"
     ".LB_Lift_lift_stage_1"),
    ("TrackSet straight",
     "/Game/LineBoss/Candidates/Spacecraft/TrackSet_v002/"
     "LB_Track_straight/StaticMeshes/LB_Track_straight"
     ".LB_Track_straight"),
    ("Drone CargoLift (remade pair)",
     "/Game/LineBoss/Candidates/Spacecraft/Drones_v001/"
     "LB_Drone_cargo_drone/StaticMeshes/LB_Drone_cargo_drone"
     ".LB_Drone_cargo_drone"),
    ("Drone Assembly (remade pair)",
     "/Game/LineBoss/Candidates/Spacecraft/Drones_v001/"
     "LB_Drone_assembly_drone/StaticMeshes/LB_Drone_assembly_drone"
     ".LB_Drone_assembly_drone"),
    ("Carrier bundled_stock",
     "/Game/LineBoss/Candidates/Spacecraft/Carriers_v001/"
     "LB_Carrier_bundled_stock/StaticMeshes/LB_Carrier_bundled_stock"
     ".LB_Carrier_bundled_stock"),
]

for label, path in CHECK:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if mesh is None:
        unreal.log_error("AUDIT %-30s NOT FOUND at %s" % (label, path))
        continue
    tris = mesh.get_num_triangles(0)
    b = mesh.get_bounds().box_extent
    unreal.log("AUDIT %-30s tris=%-6d extent=%.2fx%.2fx%.2fm"
               % (label, tris, b.x*0.02, b.y*0.02, b.z*0.02))
