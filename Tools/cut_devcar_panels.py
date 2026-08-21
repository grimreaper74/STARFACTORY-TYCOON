"""Cut the 11 WIP stamped panels from the dev car mesh.

Owner scope: Meshy for cars and panels only - so the production
line's stamped panels become regions of his car (8k LOD), exported
under the original WIP panel names for in-place asset replacement.
Each panel recentres to a floor-centre pivot.
"""
import sys

import bpy

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit  # noqa: E402

SRC = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "SourceAssets/Candidate/DevCar_v003/SM_LB_DevCar_ConceptLOD2_v003/"
       "SM_LB_DevCar_ConceptLOD2_v003.fbx")
OUT = "DevCarPanels_v001/"

# name -> (xmin, xmax, ymin, ymax, zmin, zmax) in car-local metres
# (car centred on origin: x -2.18..2.18 nose->tail, y +-0.99, z 0..1.47)
REGIONS = {
    "SM_LB_C2040_HOOD_PANEL_v001": (-2.10, -1.02, -0.86, 0.86, 0.55, 1.10),
    "SM_LB_C2040_ROOF_PANEL_v001": (-0.45, 1.25, -0.80, 0.80, 1.28, 1.60),
    "SM_LB_C2040_DOOR_FRONT_LEFT_v001": (-0.88, 0.15, -1.05, -0.78,
                                         0.22, 1.05),
    "SM_LB_C2040_DOOR_FRONT_RIGHT_v001": (-0.88, 0.15, 0.78, 1.05,
                                          0.22, 1.05),
    "SM_LB_C2040_DOOR_REAR_LEFT_v001": (0.15, 1.08, -1.05, -0.78,
                                        0.22, 1.05),
    "SM_LB_C2040_DOOR_REAR_RIGHT_v001": (0.15, 1.08, 0.78, 1.05,
                                         0.22, 1.05),
    "SM_LB_C2040_FENDER_FRONT_LEFT_v001": (-2.05, -0.88, -1.05, -0.70,
                                           0.30, 1.00),
    "SM_LB_C2040_FENDER_FRONT_RIGHT_v001": (-2.05, -0.88, 0.70, 1.05,
                                            0.30, 1.00),
    "SM_LB_C2040_QUARTER_PANEL_LEFT_v001": (1.08, 2.05, -1.05, -0.68,
                                            0.28, 1.15),
    "SM_LB_C2040_QUARTER_PANEL_RIGHT_v001": (1.08, 2.05, 0.68, 1.05,
                                             0.28, 1.15),
    "SM_LB_C2040_TAILGATE_PANEL_v001": (1.75, 2.20, -0.80, 0.80,
                                        0.50, 1.30),
}


def load_car():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    car = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    bpy.ops.object.transform_apply(location=True, rotation=True,
                                   scale=True)
    # FBX may arrive in centimetres; normalise to metres.
    if car.dimensions.x > 100.0:
        car.scale = (0.01, 0.01, 0.01)
        bpy.ops.object.select_all(action="SELECT")
        bpy.context.view_layer.objects.active = car
        bpy.ops.object.transform_apply(scale=True)
    return car


for name, (x0, x1, y0, y1, z0, z1) in REGIONS.items():
    car = load_car()
    mesh = car.data
    doomed = [p.index for p in mesh.polygons
              if not (x0 <= p.center.x <= x1 and y0 <= p.center.y <= y1
                      and z0 <= p.center.z <= z1)]
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in doomed],
                     context="FACES")
    bm.to_mesh(mesh)
    bm.free()
    if len(mesh.polygons) < 10:
        print("PANEL EMPTY", name, len(mesh.polygons))
        continue
    # Recentre: floor-centre pivot.
    vs = [car.matrix_world @ v.co for v in mesh.vertices]
    cx_ = (min(v.x for v in vs) + max(v.x for v in vs)) / 2.0
    cy_ = (min(v.y for v in vs) + max(v.y for v in vs)) / 2.0
    mz = min(v.z for v in vs)
    car.location = (-cx_, -cy_, -mz)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = car
    bpy.ops.object.transform_apply(location=True)
    car.name = name
    print("PANEL", name, len(mesh.polygons))
    kit.export(name, OUT + name)
print("PANELS CUT")
