"""Build the new clean S07 inspection/unload support cell; local +X is panel flow."""
import bpy, math
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/Candidate/PressTrains/S07_InspectionUnload/NewPortal_v949"
RENDERS = ROOT / "Saved/ValidationScreenshots/SourceAssets/S07_NewPortal_v949"
OUT.mkdir(parents=True, exist_ok=True); RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, colour, metallic=0.0, rough=0.35):
    m=bpy.data.materials.new(name); m.diffuse_color=(*colour,1)
    m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*colour,1); p.inputs['Metallic'].default_value=metallic; p.inputs['Roughness'].default_value=rough
    return m
GREEN=mat('CA_S07_Emerald',(0.018,0.19,0.105),0.55,0.28)
DARK=mat('CA_S07_Graphite',(0.025,0.032,0.036),0.65,0.25)
YELLOW=mat('CA_S07_SafetyYellow',(0.95,0.55,0.025),0.45,0.23)
STEEL=mat('CA_S07_BrushedSteel',(0.42,0.47,0.50),0.88,0.19)
GREY=mat('CA_S07_CabinetGrey',(0.36,0.40,0.42),0.55,0.28)
BLACK=mat('CA_S07_RubberBlack',(0.008,0.010,0.012),0.1,0.38)
GLASS=mat('CA_S07_SensorGlass',(0.02,0.22,0.30),0.35,0.12)

parts=[]
def cube(name, loc, scale, material, bevel=0.035):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=(scale[0]/2,scale[1]/2,scale[2]/2)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('FabricatedEdge','BEVEL'); mod.width=bevel; mod.segments=2
    o.data.materials.append(material); parts.append(o); return o
def cyl(name, loc, radius, depth, material, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.materials.append(material); parts.append(o); return o

# Grounded skid and straight-through roller receiving table (7.0 m station envelope).
cube('S07_Base_Left', (0,-1.45,0.11),(6.8,0.22,0.22),DARK)
cube('S07_Base_Right',(0, 1.45,0.11),(6.8,0.22,0.22),DARK)
for x in (-3.2,-1.6,0,1.6,3.2): cube(f'S07_Base_Tie_{x}',(x,0,0.12),(0.18,3.1,0.24),DARK)
for i,x in enumerate([ -2.8,-2.4,-2.0,-1.6,-1.2,-0.8,-0.4,0,0.4,0.8,1.2,1.6,2.0,2.4,2.8]):
    cyl(f'S07_Roller_{i:02d}',(x,0,0.72),0.105,2.35,STEEL,rot=(math.radians(90),0,0))
cube('S07_Table_LeftRail',(0,-1.25,0.67),(6.2,0.16,0.34),GREEN)
cube('S07_Table_RightRail',(0,1.25,0.67),(6.2,0.16,0.34),GREEN)

# Inspection portal with twin sensor rails, cameras and readable task lighting.
for y in (-1.62,1.62):
    cube(f'S07_Portal_Post_{y}',(0,y,2.25),(0.34,0.34,4.5),GREEN)
    cube(f'S07_Portal_Foot_{y}',(0,y,0.10),(0.85,0.75,0.20),DARK)
cube('S07_Portal_Header',(0,0,4.38),(0.42,3.65,0.42),GREEN)
cube('S07_SensorRail_Front',(-0.34,0,3.58),(0.20,3.15,0.20),DARK)
cube('S07_SensorRail_Rear',(0.34,0,3.58),(0.20,3.15,0.20),DARK)
for i,y in enumerate((-1.05,-0.35,0.35,1.05)):
    cube(f'S07_Camera_{i}',(-0.34,y,3.38),(0.22,0.28,0.18),GLASS)
    cyl(f'S07_Light_{i}',(0.34,y,3.38),0.07,0.30,STEEL,rot=(math.radians(90),0,0))

# Side robot plinth for the retained articulated unload arm; table remains unobstructed.
cube('S07_RobotPlinth',(0,2.55,0.34),(1.65,1.55,0.68),DARK)
cube('S07_RobotDockPlate',(0,2.55,0.72),(1.25,1.15,0.10),STEEL)

# Receiving stillage/table beyond inspection and electrical/HMI modules.
cube('S07_OutfeedDeck',(2.45,0,0.56),(1.15,2.35,0.18),GREY)
cube('S07_ElectricalCabinet',(-1.55,-2.45,1.12),(0.85,0.62,2.05),GREY)
cube('S07_HMI_Pedestal',(1.45,-2.45,0.95),(0.28,0.28,1.65),GREY)
hmi=cube('S07_HMI_Screen',(1.45,-2.43,1.83),(0.72,0.22,0.48),DARK); hmi.rotation_euler[1]=math.radians(-12)
cube('S07_HMI_Glass',(1.45,-2.30,1.84),(0.50,0.04,0.28),GLASS,0.01)

# Safety fencing along service sides, leaving both flow ends open.
for y in (-3.0,3.0):
    cube(f'S07_FenceTop_{y}',(0,y,1.75),(6.6,0.07,0.07),YELLOW,0.01)
    cube(f'S07_FenceMid_{y}',(0,y,0.95),(6.6,0.05,0.05),YELLOW,0.01)
    for x in (-3.2,-2.0,-0.8,0.8,2.0,3.2): cube(f'S07_FencePost_{y}_{x}',(x,y,0.95),(0.07,0.07,1.9),YELLOW,0.01)

# Four guarded corner bollards.
for x,y in ((-3.25,-2.8),(-3.25,2.8),(3.25,-2.8),(3.25,2.8)):
    cyl(f'S07_Bollard_{x}_{y}',(x,y,0.55),0.11,1.1,YELLOW)

# Apply modifiers before export and set predictable authored origin.
bpy.context.view_layer.objects.active=parts[0]
for o in parts:
    o.select_set(True); bpy.context.view_layer.objects.active=o
    for mod in list(o.modifiers):
        try: bpy.ops.object.modifier_apply(modifier=mod.name)
        except: pass
    o.select_set(False)

blend=OUT/'Cairnwell_S07_InspectionUnload_NewPortal_v949.blend'
glb=OUT/'Cairnwell_S07_InspectionUnload_NewPortal_v949.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.join(); portal_export=bpy.context.object; portal_export.name='S07_InspectionUnload_StaticPortal_v949'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True)

# Neutral studio rendering.
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-0.01)); floor=bpy.context.object; floor.data.materials.append(mat('StudioFloor',(0.12,0.13,0.14),0,0.65))
world=bpy.data.worlds.new('S07_StudioWorld'); bpy.context.scene.world=world; world.color=(0.025,0.025,0.025)
for loc,energy,size in [((-5,-6,8),1700,5),((4,4,7),1300,4),((0,-1,10),900,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=energy; l.data.shape='DISK'; l.data.size=size
def render(name,cam_loc,target,focal=52):
    bpy.ops.object.camera_add(location=cam_loc); cam=bpy.context.object; bpy.context.scene.camera=cam; cam.data.lens=focal
    direction=Vector(target)-cam.location; cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    s=bpy.context.scene; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=1600; s.render.resolution_y=1000; s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'; s.render.filepath=str(RENDERS/name); s.render.film_transparent=False
    bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam,do_unlink=True)
render('s07_new_portal_front.png',(-8,-8,5),(0,0,1.4),55)
render('s07_new_portal_side.png',(-9,0,3.2),(0,0,1.4),58)
render('s07_new_portal_elevated.png',(-7,-7,7),(0,0,1.1),52)
print(f'S07_NEW_PORTAL_V949_PASS parts={len(parts)} blend={blend} glb={glb}')
