"""Build a separate reusable Industrial Detail Library from split Meshy parts.

Inputs are linked/read then copied; no source file is saved or changed.  Every
library object is standalone, local-origin, NoCollision visual geometry.
"""
import bpy, bmesh, os, json
from mathutils import Vector

PROJECT=r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8"
OUT=os.path.join(PROJECT,'SourceAssets','Shared','CairnwellIndustrialDetailLibrary_v001')
BLEND=os.path.join(OUT,'CW_IndustrialDetailLibrary_v001.blend')
RENDERS=os.path.join(OUT,'ValidationRenders')
MANIFEST=os.path.join(OUT,'detail_library_manifest_v001.json')

ROOF=r"C:\\Users\\greg_\\Downloads\\Meshy_AI__0813061552_part-segmentation.blend"
OP=r"C:\\Users\\greg_\\Downloads\\Meshy_AI__0813062913_part-segmentation.blend"
COL='CW_IndustrialDetailLibrary_v001'

# Components whose visual function is clear in the split sources.  No whole
# machine panels/bodies, process equipment, or unrecognisable fragments.
SPECS=[
 (ROOF,'model_part0','CW_Detail_Cable_GlandStrip_A','Cable', 'roof skin split: small external gland/service fitting'),
 (ROOF,'model_part1','CW_Detail_Bracket_ServiceLug_L','Bracket','roof skin split: left fabricated service lug'),
 (ROOF,'model_part2','CW_Detail_Bracket_ServiceLug_R','Bracket','roof skin split: right fabricated service lug'),
 (ROOF,'model_part3','CW_Detail_Guard_LongRail_L','Guard','roof skin split: long formed guard/trim rail'),
 (ROOF,'model_part5','CW_Detail_Bumper_CrossRail_A','Guard','roof skin split: cross bumper/protective trim'),
 (OP,'model_part0','CW_Detail_Hinge_MicroStrip_A','Hinge','operator skin split: small hinge/retainer strip'),
 (OP,'model_part1','CW_Detail_Handle_RecessedTall_A','Handle','operator skin split: recessed vertical service handle'),
 (OP,'model_part2','CW_Detail_Latch_Tall_A','Latch','operator skin split: narrow quarter-turn/latch trim'),
 (OP,'model_part5','CW_Detail_ServiceBox_Compact_A','ServiceBox','operator skin split: compact control/service housing'),
 (OP,'model_part6','CW_Detail_EStop_ControlCap_A','Control','operator skin split: raised control cap/housing'),
 (OP,'model_part7','CW_Detail_Hinge_Long_A','Hinge','operator skin split: long enclosure hinge'),
 (OP,'model_part9','CW_Detail_Vent_FilterFrame_A','Vent','operator skin split: shallow vent/filter frame'),
 (OP,'model_part10','CW_Detail_Cable_JunctionBlock_A','Cable','operator skin split: small cable/junction block'),
 (OP,'model_part12','CW_Detail_Handle_Long_A','Handle','operator skin split: long recessed handle/edge pull'),
]

def coll(name):
 c=bpy.data.collections.get(name)
 if not c:c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
 return c
def mat(name,c,metal=.4,rough=.35):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;return m
MATS={'Graphite':mat('CW_M_Graphite',(.016,.018,.021),.72,.28),'WarmWhite':mat('CW_M_WarmWhite',(.894,.880,.835),.45,.34),'Green':mat('CW_M_CairnwellGreen',(.015,.070,.054),.35,.32),'Steel':mat('CW_M_Steel',(.40,.43,.45),.88,.24),'Black':mat('CW_M_ServiceBlack',(.003,.005,.006),.35,.43)}

def append_object(path,name):
 with bpy.data.libraries.load(path,link=False) as (frm,to):
  if name not in frm.objects:raise RuntimeError('Missing '+name+' in '+path)
  to.objects=[name]
 return to.objects[0]

def clean_and_centre(o):
 # Remove loose vertices/edges and rebuild clean outward normals on the copy.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 vs=[v.co for v in o.data.vertices];lo=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)));hi=Vector((max(v.x for v in vs),max(v.y for v in vs))); # intentionally unpack next

def extract(path,part,name,category,note,c):
 src=append_object(path,part);o=src.copy();o.data=src.data.copy();bpy.data.objects.remove(src,do_unlink=True);c.objects.link(o);o.name=name;o.data.name=name+'_Mesh'
 # Source objects have identity transforms; apply defensively and establish a sensible centred local origin.
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.select_set(False)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 vs=[v.co for v in o.data.vertices];lo=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)));hi=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)));centre=(lo+hi)/2
 for v in o.data.vertices:v.co-=centre
 o.data.update();dim=hi-lo
 # The library default places the mounting plane on local -Y; future use may rotate.
 o.data.materials.clear();default='Steel' if category in ('Hinge','Bracket','Guard') else ('Black' if category in ('Cable','Control') else 'Graphite');o.data.materials.append(MATS[default])
 o['FamilyId']='CW_IndustrialDetail';o['Category']=category;o['SourceModel']=path;o['SourceObject']=part;o['SourceNote']=note;o['CollisionPolicy']='NoCollision';o['LocalOrigin']='bounding-box centre; mounting plane typically -Y';o['RuntimeStatus']='SOURCE_REUSABLE_CANDIDATE_ONLY'
 # Validate gross mesh health.
 bm=bmesh.new();bm.from_mesh(o.data);nonmanifold=sum(1 for e in bm.edges if not e.is_manifold);faces=len(bm.faces);verts=len(bm.verts);bm.free()
 return {'name':name,'category':category,'source_model':path,'source_object':part,'note':note,'dimensions_m':[round(v,5) for v in dim],'vertices':verts,'faces':faces,'non_manifold_edges':nonmanifold,'collision':'NoCollision','status':'candidate-only'}

def stage(scene,c):
 scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world.color=(.015,.018,.02)
 floor=mat('CW_STAGE_Floor',(.12,.13,.14),0,.7)
 bpy.ops.mesh.primitive_plane_add(size=16,location=(0,0,-.01));p=bpy.context.object;p.data.materials.append(floor);[cc.objects.unlink(p) for cc in list(p.users_collection)];c.objects.link(p)
 def light(n,l,e,size):
  d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=l;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
 light('Key',(-5,5,6),1100,4);light('Fill',(5,2,4),750,4);light('Rim',(0,-5,5),900,3)
 d=bpy.data.cameras.new('CW_DETAIL_CAMERA');d.lens=52;cam=bpy.data.objects.new('CW_DETAIL_CAMERA',d);c.objects.link(cam);scene.camera=cam;return cam
def render_thumbs(scene,cam,objects):
 os.makedirs(RENDERS,exist_ok=True)
 for o in objects:
  o.hide_render=False
  maxdim=max(o.dimensions);cam.location=(maxdim*2.6,-maxdim*2.8,maxdim*1.9);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(RENDERS,o.name+'.png');bpy.ops.render.render(write_still=True)
  print('THUMB|'+scene.render.filepath)
def main():
 c=coll(COL);stage_c=coll('CW_IndustrialDetailLibrary_STAGE_v001');records=[];objs=[]
 for spec in SPECS:
  rec=extract(*spec,c);records.append(rec);objs.append(bpy.data.objects[rec['name']])
 s=bpy.context.scene;s['LibraryName']='Cairnwell Industrial Detail Library v001';s['Scope']='Source-only reusable detail candidates. Not validated for Unreal/runtime.';os.makedirs(OUT,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=BLEND,copy=False);cam=stage(s,stage_c);render_thumbs(s,cam,objs);bpy.ops.wm.save_as_mainfile(filepath=BLEND,copy=False)
 with open(MANIFEST,'w',encoding='utf-8') as f:json.dump({'library':'CW_IndustrialDetailLibrary_v001','status':'candidate-only','source_files_unchanged':True,'components':records},f,indent=2)
 print('LIBRARY_SAVED|'+BLEND);print('MANIFEST|'+MANIFEST);print('COUNT|'+str(len(records)))
if __name__=='__main__':main()
