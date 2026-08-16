"""PR005 v006 non-destructive visual-skin review derivative.

Source v812 remains immutable.  In this derivative:
  * a display-only shell duplicate omits six legacy roof sheets;
  * two supplied Meshy roof panels fill that exact opening;
  * the supplied operator-side Meshy service-bay is a shallow exterior overlay.
All new geometry is visual-only, has no functional pivot and is marked NoCollision.
"""
import bpy, bmesh, os
from mathutils import Vector

PROJECT = r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8"
ROOF = r"C:\\Users\\greg_\\Downloads\\Meshy_AI__0813061552_part-segmentation.blend"
OPERATOR = r"C:\\Users\\greg_\\Downloads\\Meshy_AI_B_—_Operator_side_s_0813064000_generate.blend"
UTILITIES = r"C:\\Users\\greg_\\Downloads\\Meshy_AI_C_—_Utilities_side__0813063947_generate.blend"
COIL_ENTRY = r"C:\\Users\\greg_\\Downloads\\Meshy_AI_D_—_Coil_entry_surr_0813064007_generate.blend"
STRIP_EXIT = r"C:\\Users\\greg_\\Downloads\\Meshy_AI_E_—_Strip_exit_surr_0813064015_generate.blend"
OUT = os.path.join(PROJECT, "SourceAssets", "Candidate", "PressShop", "PR005", "ArtSkin_v009_MeshyFullSkinColoured")
OUT_BLEND = os.path.join(OUT, "PR005_CairnwellMeshySkin_v009.blend")
RENDERS = os.path.join(OUT, "Renders")
SKIN = "97_PR005_MESHY_VISUAL_SKIN_V009"
STAGE = "98_PR005_MESHY_VISUAL_REVIEW_STAGE_V009"
SHELL_NAME = "SM_CA_MW_PR005_EnclosureShell_Static_v002"

def state(o):
    return (o.type, o.parent.name if o.parent else '', tuple(round(v, 6) for v in o.location), tuple(round(v, 6) for v in o.rotation_euler), tuple(round(v, 6) for v in o.scale))

def collection(name):
    c=bpy.data.collections.get(name)
    if not c: c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c

def move(o,c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o)

def material(name, rgb, metallic=.4, rough=.34):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value=(*rgb,1); b.inputs['Metallic'].default_value=metallic; b.inputs['Roughness'].default_value=rough
    return m

def append_objects(path):
    # Segmentation exports use model_partXX names while retained generate
    # masters use one differently named mesh. Both are legitimate sources.
    with bpy.data.libraries.load(path, link=False) as (frm,to): to.objects=list(frm.objects)
    result=[o for o in to.objects if o and o.type=='MESH']
    if not result: raise RuntimeError('No Meshy parts found in '+path)
    return result

def remove_roof_sheets(mesh):
    """Strip the six detached legacy sheets from a *display duplicate* only."""
    bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); seen=set(); kill=[]
    for v in bm.verts:
        if v in seen: continue
        todo=[v]; seen.add(v); comp=[]
        while todo:
            q=todo.pop(); comp.append(q)
            for e in q.link_edges:
                w=e.other_vert(q)
                if w not in seen: seen.add(w); todo.append(w)
        lo=[min(q.co[i] for q in comp) for i in range(3)]; hi=[max(q.co[i] for q in comp) for i in range(3)]
        if len(comp)==56 and abs(lo[0]+2.675)<.003 and abs(hi[0]-2.675)<.003 and lo[1]>=-1.071 and hi[1]<=5.071 and lo[2]>=3.429 and hi[2]<=3.531: kill.extend(comp)
    if len(kill)!=336: raise RuntimeError('Expected six legacy roof islands /336 verts, got %d'%len(kill))
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(mesh); bm.free(); mesh.update()

def align_roof_crossbeam(mesh):
    """On the display duplicate, move the existing crossbeam onto the new seam.

    Existing beam spans y=2.120..2.280. It moves -0.200m so that its centre
    lies at y=2.000, exactly above the two Meshy roof-panel edges.
    """
    bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); seen=set(); hits=[]
    for v in bm.verts:
        if v in seen: continue
        todo=[v];seen.add(v);component=[]
        while todo:
            q=todo.pop();component.append(q)
            for e in q.link_edges:
                w=e.other_vert(q)
                if w not in seen:seen.add(w);todo.append(w)
        lo=[min(q.co[i] for q in component) for i in range(3)];hi=[max(q.co[i] for q in component) for i in range(3)]
        if (len(component)==56 and abs(lo[1]-2.12)<.003 and abs(hi[1]-2.28)<.003):
            hits.extend(component)
    if len(hits)!=336: raise RuntimeError('Expected complete frame set /336 verts, got %d'%len(hits))
    bmesh.ops.translate(bm, verts=hits, vec=Vector((0,-.200,0)))
    bm.to_mesh(mesh);bm.free();mesh.update()
    print('DISPLAY_ROOF_CROSSBEAM_ALIGNED|y=2.000')

def make_display_shell(c):
    source=bpy.data.objects[SHELL_NAME]
    visual=source.copy(); visual.data=source.data.copy(); visual.name='VISUAL_PR005_EnclosureShell_RoofSheetsReplaced_v006'
    c.objects.link(visual); remove_roof_sheets(visual.data); align_roof_crossbeam(visual.data)
    visual['visual_display_duplicate']=True; visual['collision_policy']='NoCollision'; visual['purpose']='Presentation-only duplicate with six legacy roof sheets removed.'
    # Keep original core present for engineering and collision inspection but do not double-render it.
    source.hide_render=True
    return visual

def bounds(objs):
    vs=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
    lo=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs))); hi=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)))
    return lo,hi,(lo+hi)/2

def root_copy_parts(c, parts, label, location, scales, mats, source_hash):
    lo,hi,centre=bounds(parts)
    root=bpy.data.objects.new(label,None); c.objects.link(root); root.location=location
    for i,src in enumerate(parts):
        o=src.copy(); o.data=src.data.copy(); o.name=label+'_Part%02d'%i; o.data.materials.clear()
        # Segmentation files already isolate components.  Retained generate
        # masters are a single mesh, but retain disconnected mechanical pieces;
        # distribute approved Cairnwell materials across those pieces.
        for m in mats: o.data.materials.append(m)
        if len(parts)>1:
            for poly in o.data.polygons: poly.material_index=i%len(mats)
        else:
            colour_master_components(o.data)
        c.objects.link(o); o.parent=root
        o.scale=scales; o.location=Vector((-centre.x*scales[0],-centre.y*scales[1],-centre.z*scales[2]))
        o['visual_skin_only']=True; o['collision_policy']='NoCollision'; o['source_sha256']=source_hash
    root['visual_skin_only']=True; root['functional_pivot']=False
    for o in parts: bpy.data.objects.remove(o,do_unlink=True)
    return root,lo,hi

def colour_master_components(mesh):
    """Apply a restrained OEM palette to disconnected generate-master pieces.

    Index 0 is warm white, 1 graphite, 2 Cairnwell green, 3 yellow, 4 steel.
    Yellow is intentionally never selected here: it remains safety-only.
    """
    bm=bmesh.new(); bm.from_mesh(mesh); bm.faces.ensure_lookup_table(); seen=set(); groups=[]
    for face in bm.faces:
        if face in seen: continue
        todo=[face]; seen.add(face); group=[]
        while todo:
            q=todo.pop();group.append(q)
            for edge in q.edges:
                for other in edge.link_faces:
                    if other not in seen: seen.add(other);todo.append(other)
        groups.append(group)
    groups.sort(key=len,reverse=True)
    # Largest fabricated body = warm white; secondary inner frame = graphite;
    # door-like following pieces receive limited green; all remaining small
    # brackets/latches use graphite or steel.
    for rank,group in enumerate(groups):
        if rank==0: index=0
        elif rank==1: index=1
        elif rank in (2,5): index=2
        elif rank%3==0: index=4
        else: index=1
        for face in group: face.material_index=index
    bm.to_mesh(mesh);bm.free();mesh.update()

def build_roof(c, mats):
    parts=append_objects(ROOF); lo,hi,centre=bounds(parts); size=hi-lo
    # Existing ready panel opening: 5.350 x 6.140 x .100m; two replacement panels.
    scales=(5.350/size.x,(6.140/2)/size.y,.100/size.z)
    for label,y in (('SKIN_PR005_RoofPanel_Lower',-1.070+6.140/4),('SKIN_PR005_RoofPanel_Upper',-1.070+3*6.140/4)):
        panel,_,_=root_copy_parts(c,parts,label,(0,y,3.530-hi.z*scales[2]),scales,mats,'2BA8ACB22CD85A1A4F38BA03927EB0978028E4C95E17ADC12395D5757B9FCF27')
        panel['installation']='One of two replacements of ready roof sheets: 5.350 x 3.070 x .100m.'
        # reload source for the second instance (the helper intentionally clears temp objects)
        if label.endswith('Lower'): parts=append_objects(ROOF); lo,hi,centre=bounds(parts); size=hi-lo

def build_operator_bay(c, mats):
    parts=append_objects(OPERATOR); lo,hi,centre=bounds(parts); size=hi-lo
    # The detailed external module is fitted as one shallow, 1.95m-long operator
    # service bay.  It occupies y=-4.55..-2.60 and z=.35..3.00, leaving the
    # operator door / HMI zones and the functional envelope intact.
    # Its original depth becomes a 100mm exterior cladding depth along -X.
    scales=(1.950/size.x,.100/size.y,2.650/size.z)
    # local X maps to world Y; local Y maps to world X (rotation Z=-90°).
    root,_,_=root_copy_parts(c,parts,'SKIN_PR005_OperatorServiceBay',(-2.842,-3.575,.35+2.650/2),scales,mats,'2042647D6D10E3EF10FD89CB875215D7D2D9630BA0A8EB6A054221B471CBB4C3')
    root.rotation_euler[2]=1.57079632679
    root['installation']='Operator-side visual access bay x=-2.892..-2.792, y=-4.550..-2.600, z=.350..3.000. Clear of HMI, operator door and moving equipment.'

def build_utilities_bay(c, mats):
    parts=append_objects(UTILITIES); lo,hi,centre=bounds(parts); size=hi-lo
    # Opposite-side service bay, kept away from the utilities door at y=.575.
    scales=(1.950/size.x,.100/size.y,2.650/size.z)
    root,_,_=root_copy_parts(c,parts,'SKIN_PR005_UtilitiesServiceBay',(2.842,-3.575,.35+2.650/2),scales,mats,'3E437D848027BBC7D21947C0417B32B8E13F5B9C19C2C8C24DD056AF92787AF8')
    root.rotation_euler[2]=-1.57079632679
    root['installation']='Utilities-side visual service bay x=+2.792..+2.892, y=-4.550..-2.600, z=.350..3.000. Clear of utilities door and all process equipment.'

def build_coil_entry(c, mats):
    parts=append_objects(COIL_ENTRY); lo,hi,centre=bounds(parts); size=hi-lo
    # Rear / coil-entry surround. Its circular reveal remains centred on the
    # headstock line; only the depth is squashed to a 160mm exterior skin.
    scales=(3.550/size.x,.160/size.y,2.500/size.z)
    root,_,_=root_copy_parts(c,parts,'SKIN_PR005_CoilEntrySurround',(0,-5.100,1.850),scales,mats,'8315AF618CC97F7392DE60F1E78CC150650178C875D3EA42A9B836302C0661EF')
    root['installation']='Coil-entry visual surround x=-1.775..+1.775, y=-5.180..-5.020, z=.600..3.100. Engineering mandrel/core remains behind the visual aperture.'

def build_strip_exit(c, mats):
    parts=append_objects(STRIP_EXIT); lo,hi,centre=bounds(parts); size=hi-lo
    # Outfeed surround is deliberately above the strip path (z ~.90m): no
    # visual element crosses the actual strip exit or threader table.
    scales=(5.350/size.x,.160/size.y,1.200/size.z)
    root,_,_=root_copy_parts(c,parts,'SKIN_PR005_StripExitSurround',(0,5.100,2.650),scales,mats,'D9618F4F11DAE5B3F44D7E82560C511071D3527839D7C0A5B75431425E473F0E')
    root['installation']='Strip-exit upper surround x=-2.675..+2.675, y=+5.020..+5.180, z=2.050..3.250. Clear of strip exit at z=.900 and threader table.'

def cube(name,loc,dim,mat,c):
    bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);move(o,c);return o

def stage(scene,c):
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world.color=(.012,.015,.017)
    cube('STAGE_PR005_Floor',(0,0,-.08),(18,24,.10),material('STAGE_PR005_FloorMat',(.18,.19,.19),0,.72),c)
    def light(n,l,e,s,t,col):
        d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=s;d.color=col;o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=l;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
    light('STAGE_Key',(-8,10,11),1700,6,(0,0,1.8),(.92,.96,1));light('STAGE_Fill',(9,1,8),1350,5,(0,0,1.5),(.84,.90,1));light('STAGE_Rim',(0,-10,9),1450,5,(0,0,1.6),(1,.87,.70))
    d=bpy.data.cameras.new('STAGE_CAMERA');d.lens=52;cam=bpy.data.objects.new('STAGE_CAMERA',d);c.objects.link(cam);scene.camera=cam;return cam

def render(scene,cam):
    os.makedirs(RENDERS,exist_ok=True)
    shots={'01_PR005_MeshySkin_v009_Front.png':(0,13.5,5),'02_PR005_MeshySkin_v009_Rear.png':(0,-13.5,5),'03_PR005_MeshySkin_v009_OperatorSide.png':(-13.5,0,5),'04_PR005_MeshySkin_v009_ServiceSide.png':(13.5,0,5),'05_PR005_MeshySkin_v009_ThreeQuarter.png':(-11.5,12.2,9),'06_PR005_MeshySkin_v009_OperatorDetail.png':(-9,-8,4.5),'07_PR005_MeshySkin_v009_Top.png':(0,0,16.5)}
    for name,loc in shots.items():
        cam.location=loc; cam.rotation_euler=(Vector((0,0,1.7))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(RENDERS,name);bpy.ops.render.render(write_still=True);print('RENDERED|'+scene.render.filepath)

def main():
    before={o.name:state(o) for o in bpy.context.scene.objects}
    c=collection(SKIN); stage_c=collection(STAGE)
    warm=material('SKIN_PR005_WarmWhite',(.894,.880,.835),.45,.34); graphite=material('SKIN_PR005_Graphite',(.016,.018,.021),.72,.28); green=material('SKIN_PR005_CairnwellGreen',(.015,.070,.054),.35,.32); yellow=material('SKIN_PR005_SafetyYellow',(.887,.545,.006),.25,.36); steel=material('SKIN_PR005_ExposedSteel',(.40,.43,.45),.88,.24)
    mats=[warm,graphite,green,yellow,steel]
    make_display_shell(c); build_roof(c,mats); build_operator_bay(c,mats); build_utilities_bay(c,mats); build_coil_entry(c,mats); build_strip_exit(c,mats)
    # Original non-shell engineering transforms/hierarchy stay exactly as loaded.
    bad=[n for n,v in before.items() if n!=SHELL_NAME and state(bpy.data.objects[n])!=v]
    if bad: raise RuntimeError('Unexpected core modification: '+', '.join(bad))
    s=bpy.context.scene;s['visual_skin_version']='PR005_MeshyFullSkinAssembly_v009';s['scope']='Visual display derivative only. Named Meshy masters fitted into their correct roof, operator, utility, coil-entry and strip-exit roles; generated-master subassemblies assigned restrained Cairnwell materials; no Unreal import; no core source write; NoCollision skins.'
    os.makedirs(OUT,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND,copy=False);cam=stage(s,stage_c);render(s,cam);bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND,copy=False)
    print('DERIVATIVE_SAVED|'+OUT_BLEND);print('ENGINEERING_SOURCE_UNCHANGED|'+str(len(before)))
if __name__=='__main__':main()
