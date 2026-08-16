"""Blender CLI: rigid hard-surface press shell replacement based on the approved four-view reference."""
from pathlib import Path
from datetime import datetime,timezone
import bpy,json,math
from mathutils import Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\Shared\RigidPressShell_v729";REVIEW=OUT/'Review';OUT.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
BLEND=OUT/'CA_MW_RigidPressShell_v729.blend';GLB=OUT/'SM_CA_MW_RigidPressShell_v729.glb';AUDIT=OUT/'RIGID_PRESS_SHELL_MANIFEST_v729.json'
if any(p.exists() for p in (BLEND,GLB,AUDIT)):raise RuntimeError('Refusing overwrite v729')
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,color,metal=.25,rough=.42):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
green=mat('CA_MW_Press_RigidGreen_v729',(0.035,0.16,0.105),.62,.34);dark=mat('CA_MW_Press_Graphite_v729',(.035,.042,.045),.72,.28);steel=mat('CA_MW_Press_MachinedSteel_v729',(.34,.38,.40),.88,.20);yellow=mat('CA_MW_Press_SafetyYellow_v729',(.95,.52,.025),.42,.28);black=mat('CA_MW_Press_RubberBlack_v729',(.008,.010,.012),.05,.58);ivory=mat('CA_MW_Press_LabelIvory_v729',(.82,.83,.78),.1,.35)
objects=[]
def box(name,loc,dims,material,bevel=.035):
 bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:m=o.modifiers.new('RigidEdgeBevel','BEVEL');m.width=bevel;m.segments=2
 o.data.materials.append(material);objects.append(o);return o
def cyl(name,loc,r,depth,material,axis='Z',verts=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name
 if axis=='X':o.rotation_euler[1]=math.radians(90)
 elif axis=='Y':o.rotation_euler[0]=math.radians(90)
 o.data.materials.append(material);objects.append(o);return o
# Monolithic rigid load path: foundation, uprights, crown and bolster.
box('PT_Rigid_BaseFoundation',(0,0,.38),(9.90,5.40,.76),green,.08)
box('PT_Rigid_BolsterBed',(0,-.15,1.00),(6.35,4.35,.48),steel,.055)
for x in (-4.05,4.05):
 box(f'PT_Rigid_Upright_{x:+.2f}',(x,0,3.55),(1.55,5.20,5.65),green,.075)
 box(f'PT_Rigid_UprightFoot_{x:+.2f}',(x,0,.88),(1.95,5.35,.58),dark,.05)
 for y in (-2.48,2.48):box(f'PT_Rigid_UprightFlange_{x:+.2f}_{y:+.2f}',(x,y,3.55),(1.90,.16,5.45),green,.025)
 for z in (1.55,2.55,3.55,4.55,5.55):box(f'PT_Rigid_Rib_{x:+.2f}_{z:.2f}',(x,-2.60,z),(1.95,.20,.18),dark,.018)
box('PT_Rigid_CrownMain',(0,0,7.05),(9.90,5.40,2.30),green,.09)
box('PT_Rigid_CrownLowerBeam',(0,0,5.98),(7.25,5.10,.42),dark,.04)
box('PT_Rigid_RamGuideHousing',(0,-.12,5.58),(5.15,4.30,.58),dark,.045)
box('PT_Rigid_RamSlide',(0,-.10,4.85),(5.00,4.00,.72),steel,.045)
# Crown panels, side drive housings and rigid service doors.
for y in (-2.63,2.63):
 box(f'PT_Rigid_CrownFace_{y:+.2f}',(0,y,7.15),(6.55,.14,1.58),green,.025)
 for x in (-3.75,-1.25,1.25,3.75):box(f'PT_Rigid_CrownFaceRib_{x:+.2f}_{y:+.2f}',(x,y*1.005,7.15),(.14,.18,1.72),dark,.015)
for x in (-4.92,4.92):
 box(f'PT_Rigid_DriveHousing_{x:+.2f}',(x,-.30,6.85),(.72,3.55,2.15),dark,.065)
 box(f'PT_Rigid_DriveCover_{x:+.2f}',(x,-2.08,6.85),(.82,.16,1.72),dark,.035)
 cyl(f'PT_Rigid_DriveBoss_{x:+.2f}',(x,-2.20,6.85),.48,.16,steel,'Y',40)
# Top-frame grid and hydraulic services.
for x in (-3.8,-1.9,0,1.9,3.8):box(f'PT_Rigid_TopLongitudinal_{x:+.1f}',(x,0,8.29),(.18,5.10,.18),dark,.02)
for y in (-2.25,-.75,.75,2.25):box(f'PT_Rigid_TopCross_{y:+.2f}',(0,y,8.31),(9.25,.16,.16),dark,.02)
for x in (-3.0,0,3.0):cyl(f'PT_Rigid_TopPipe_{x:+.1f}',(x,0,8.55),.10,4.80,steel,'Y',24)
# Bolted face plates and reinforced opening corners.
for x in (-2.9,2.9):
 box(f'PT_Rigid_OpeningPost_{x:+.1f}',(x,-2.66,3.45),(.32,.18,4.60),green,.025)
 for z in (1.35,2.10,2.85,3.60,4.35,5.10):cyl(f'PT_Rigid_Bolt_{x:+.1f}_{z:.2f}',(x,-2.80,z),.055,.10,yellow,'Y',20)
for x in (-4.45,-3.75,3.75,4.45):
 for z in (1.3,2.2,3.1,4.0,4.9,5.8,6.7,7.6):cyl(f'PT_Rigid_FrameBolt_{x:+.2f}_{z:.1f}',(x,-2.73,z),.045,.09,steel,'Y',16)
# Operator identity panels; no generated/melted lettering geometry.
box('PT_Rigid_IdentityPlate',(0,-2.74,7.28),(3.40,.10,.78),black,.025)
for i,w in enumerate((2.55,1.95)):
 box(f'PT_Rigid_IdentityBar_{i}',(0,-2.81,7.43-i*.30),(w,.035,.10),ivory,.012)
box('PT_Rigid_StationPlate',(0,-2.75,6.48),(1.10,.10,.46),black,.02)
for x in (-.32,0,.32):box(f'PT_Rigid_StationMark_{x:+.2f}',(x,-2.82,6.48),(.16,.035,.22),ivory,.01)
# Safety details and service access.
for x in (-4.68,4.68):
 for z in (1.55,2.25,2.95,3.65,4.35):box(f'PT_Rigid_SafetyStripe_{x:+.2f}_{z:.2f}',(x,-2.76,z),(.28,.08,.10),yellow,.01)
for y in (-2.1,-.7,.7,2.1):cyl(f'PT_Rigid_TieRod_{y:+.1f}',(0,y,7.20),.095,9.35,steel,'X',24)
# Apply modifiers and stable normals.
for o in objects:
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 for p in o.data.polygons:p.use_smooth=False
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_materials='EXPORT',export_normals=True,export_apply=True)
# Textured Blender review.
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.012,.016,.02,1);bg.inputs['Strength'].default_value=.32
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;d.color=color;a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(Vector((0,0,4))-a.location).to_track_quat('-Z','Y').to_euler()
area('Key',(-11,-10,14),3000,11,(1,.90,.76));area('Fill',(11,-5,10),2300,10,(.72,.84,1));area('Rim',(0,8,13),2600,11,(.78,1,.84))
def render(name,loc,target):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);scene.collection.objects.link(c);scene.camera=c;d.lens=58;c.location=Vector(loc);c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(REVIEW/name);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
render('RigidPressShell_operator_hero_v729.png',(-13,-14,10),(0,0,4));render('RigidPressShell_operator_front_v729.png',(0,-20,4.4),(0,0,4));render('RigidPressShell_service_rear_v729.png',(11,13,10),(0,0,4))
tris=sum(len(p.vertices)-2 for o in objects for p in o.data.polygons)
AUDIT.write_text(json.dumps({'revision':'v729','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'NEW_RIGID_HARD_SURFACE_PRESS_SHELL__BLENDER_VISUAL_REVIEW_REQUIRED__NOT_IMPORTED_TO_UNREAL','source_reference':'ChatGPT Image Aug 8, 2026, 09_17_27 AM (2).png','rejected_meshy_master':'SM_CA_MW_PT_Shared_StaticPressShell_LOD0_v639.glb','reason_rejected':'melted/sagging geometry baked into raw Meshy output','dimensions_m':[9.9,5.4,8.65],'object_count':len(objects),'triangle_count':tris,'materials':[m.name for m in (green,dark,steel,yellow,black,ivory)],'blend':str(BLEND),'glb':str(GLB),'renders':[str(p) for p in sorted(REVIEW.glob('*.png'))],'meshy_credits_used':0,'unreal_import_started':False},indent=2),encoding='utf-8')
print('LINE_BOSS_RIGID_PRESS_SHELL_V729_PASS')
