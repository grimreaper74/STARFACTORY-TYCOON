"""Build v134 directly from v124 with a south-side AGV logistics route.

v133 remains rejected evidence and is never used as a parent. This successor
reuses only the independently validated source FBX and the v133 builder logic.
"""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr003_pr004_coil_agv_candidate_v133.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v133", "v134").replace("V133", "V134")
code = code.replace(
    "AGV = (-5545.0, -2000.0)",
    "AGV = (-6200.0, -2700.0)")

old_route = '''# 3.2 m candidate route is marked, not asserted as approved engineering data.
route = [floor_bar("RouteBoundaryNorth", (-6260,-1840,8.7), (1880,8,1.0), yellow_material),
         floor_bar("RouteBoundarySouth", (-6260,-2160,8.7), (1880,8,1.0), yellow_material)]
for index, x in enumerate((-7040,-6760,-6480,-6200,-5920,-5640), start=1):
    route.append(floor_bar(f"RouteCentreDash_{index:02d}", (x,-2000,8.75), (145,10,1.1), route_material))'''
new_route = '''# 3.2 m candidate route is marked, not asserted as approved engineering data.
# It runs south of the front coil row, matching the owner-provided proposed
# revision, then turns north to the PR004 west dock without using the pedestrian lane.
route = [floor_bar("RouteBoundaryNorth", (-6370,-2540,8.7), (1660,8,1.0), yellow_material),
         floor_bar("RouteBoundarySouth", (-6370,-2860,8.7), (1660,8,1.0), yellow_material),
         floor_bar("RouteTurnWest", (-5710,-2350,8.7), (8,700,1.0), yellow_material),
         floor_bar("RouteTurnEast", (-5390,-2350,8.7), (8,700,1.0), yellow_material)]
for index, x in enumerate((-7040,-6760,-6480,-6200,-5920,-5640), start=1):
    route.append(floor_bar(f"RouteCentreDash_{index:02d}", (x,-2700,8.75), (145,10,1.1), route_material))
for index, y in enumerate((-2620,-2380,-2140), start=1):
    route.append(floor_bar(f"RouteTurnDash_{index:02d}", (-5550,y,8.75), (10,120,1.1), route_material))'''
if old_route not in code:
    raise RuntimeError("v133 route block changed")
code = code.replace(old_route, new_route)

needle = '''deck.tags = tags("LB.Asset.Candidate.v134", "LB.Asset.CandidateNotPromoted", "LB.Vehicle.CoilAGV.LiftDeck",
                 "LB.Motion.AGVDockLift", "LB.Motion.Range.80mm.TBC", "LB.Runtime.Authority.NotYetBound")'''
material_binding = needle + '''

# Bind controlled Unreal materials per imported slot. Component overrides keep
# v133 evidence and the reusable source meshes immutable.
controlled_materials = {
    "FabricatedCharcoal": library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031"),
    "DeckSteel": library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031"),
    "SafetyYellow": library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031"),
    "HighLoadRubber": library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber"),
    "WheelPolyurethane": library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber"),
    "SensorGlass": library.load_asset("/Game/LineBoss/Stations/Press/PR004/Candidate_v011/LayeredMaterials/MI_LB_PR004_Layered_SensorBlue_v011"),
    "BlueDirectionLight": library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Blue"),
    "StatusGreen": library.load_asset("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_StatusGreen_R_v002"),
    "BeaconAmber": library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031"),
    "EStopRed": library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_SafetyRed"),
    "CairnwellMark": library.load_asset("/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025/M_CA_MW_PT_LabelWhiteLayered_v025"),
}
if any(value is None for value in controlled_materials.values()):
    raise RuntimeError("Missing controlled AGV material")
material_bindings = []
for actor, mesh in ((chassis, chassis_mesh), (deck, deck_mesh)):
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        match = next((value for token, value in controlled_materials.items() if token in slot_name), None)
        if match is None:
            raise RuntimeError(f"Unmapped AGV material slot: {slot_name}")
        actor.static_mesh_component.set_material(index, match)
        material_bindings.append({"actor":actor.get_actor_label(),"slot":slot_name,"material":match.get_path_name()})
chassis.tags = tags(*[str(t) for t in chassis.tags], "LB.Visual.MaterialHierarchy.Controlled.v134", "LB.Route.SouthLogistics.TBC")
deck.tags = tags(*[str(t) for t in deck.tags], "LB.Visual.MaterialHierarchy.Controlled.v134", "LB.Route.SouthLogistics.TBC")'''
if needle not in code:
    raise RuntimeError("v134 material injection point missing")
code = code.replace(needle, material_binding)

old_cameras = '''cameras = [camera("LoadedApproach", (-6680,-930,560), (-5620,-2000,115), 47.0),
           camera("DockAndPR004", (-6180,-1050,520), (-5350,-1980,110), 42.0),
           camera("RouteOverview", (-6450,-2000,1750), (-6200,-2000,0), 58.0)]'''
new_cameras = '''cameras = [camera("SouthRouteOverview", (-6900,-3700,650), (-6100,-2450,110), 48.0),
           camera("AGVLoadedClose", (-6710,-3400,365), (-6200,-2700,105), 43.0),
           camera("RouteTurnAndPR004", (-6200,-3650,650), (-5500,-2250,100), 47.0)]'''
if old_cameras not in code:
    raise RuntimeError("v133 camera block changed")
code = code.replace(old_cameras, new_cameras)
code = code.replace('"agv_dock_location_cm":[AGV[0],AGV[1]]', '"agv_staged_location_cm":[AGV[0],AGV[1]]')
code = code.replace('"fixed_cameras":[a.get_actor_label() for a in cameras]', '"controlled_material_bindings":material_bindings,"fixed_cameras":[a.get_actor_label() for a in cameras]')
exec(compile(code, str(source), "exec"), {"__name__":"__main__","__file__":str(source)})
