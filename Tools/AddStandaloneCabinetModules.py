"""Add intact existing Cairnwell cabinet/HMI masters to the shared library.

The master source blend is only appended from; it is never saved or modified.
The library instances are visual-module candidates, not runtime assets.
"""
import bpy, json, os
from mathutils import Vector

PROJECT = r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8"
LIB = os.path.join(PROJECT, "SourceAssets", "Shared", "CairnwellIndustrialDetailLibrary_v001")
BLEND = os.path.join(LIB, "CW_IndustrialDetailLibrary_v001.blend")
MASTER = os.path.join(PROJECT, "SourceAssets", "Shared", "FactoryAssetLibrary", "MeshyCabinetHMI_v632", "CA_Factory_Cabinet_HMI_MeshyMasters_v632.blend")
MANIFEST = os.path.join(LIB, "standalone_module_manifest_v001.json")
RENDERS = os.path.join(LIB, "ValidationRenders")
COLLECTION = "CW_StandaloneModules_v001"
SPECS = [
    ("SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632", "CW_Module_ElectricalCabinet_MeshyMaster_v632", "Electrical cabinet / service enclosure"),
    ("SM_CA_Factory_OperatorHMI_MeshyMaster_v632", "CW_Module_OperatorHMI_MeshyMaster_v632", "Operator HMI console"),
]

def collection(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def append_obj(name):
    with bpy.data.libraries.load(MASTER, link=False) as (frm, to):
        if name not in frm.objects:
            raise RuntimeError("Missing master object " + name)
        to.objects = [name]
    return to.objects[0]

def bounds(o):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi

def staging(scene):
    existing = bpy.data.collections.get("CW_STANDALONE_THUMB_STAGE")
    if existing:
        return existing, bpy.data.objects.get("CW_STANDALONE_THUMB_CAMERA")
    c = collection("CW_STANDALONE_THUMB_STAGE")
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1200, 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.018, .021, .023)
    def material(name, colour):
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = (*colour, 1); b.inputs["Roughness"].default_value = .7
        return m
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -.02))
    floor = bpy.context.object; floor.name = "CW_STANDALONE_THUMB_FLOOR"; floor.data.materials.append(material("CW_ThumbFloor", (.13, .14, .14)))
    for old in list(floor.users_collection): old.objects.unlink(floor)
    c.objects.link(floor)
    def light(name, location, energy, size):
        d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = "DISK"; d.size = size
        o = bpy.data.objects.new(name, d); c.objects.link(o); o.location = location
        o.rotation_euler = (Vector((0, 0, .8)) - o.location).to_track_quat("-Z", "Y").to_euler()
    light("CW_Thumb_Key", (-4, 5, 5), 1100, 4); light("CW_Thumb_Fill", (4, 2, 4), 800, 4); light("CW_Thumb_Rim", (0, -4, 4), 1000, 3)
    d = bpy.data.cameras.new("CW_STANDALONE_THUMB_CAMERA")
    cam = bpy.data.objects.new("CW_STANDALONE_THUMB_CAMERA", d); c.objects.link(cam); scene.camera = cam
    return c, cam

def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    c = collection(COLLECTION)
    records = []
    for src_name, target_name, role in SPECS:
        if bpy.data.objects.get(target_name):
            o = bpy.data.objects[target_name]
        else:
            src = append_obj(src_name)
            o = src.copy(); o.data = src.data.copy(); bpy.data.objects.remove(src, do_unlink=True)
            o.name = target_name; o.data.name = target_name + "_Mesh"; c.objects.link(o)
        lo, hi = bounds(o)
        # Source orientations are retained, as these are intact placeable modules.
        o["FamilyId"] = "CW_StandaloneIndustrialModule"
        o["Role"] = role
        o["SourceModel"] = MASTER
        o["SourceObject"] = src_name
        o["CollisionPolicy"] = "NoCollision"
        o["RuntimeStatus"] = "SOURCE_REUSABLE_CANDIDATE_ONLY"
        o["ReuseRule"] = "Keep intact; use only as role-matched visual module."
        records.append({"name": target_name, "role": role, "source_model": MASTER, "source_object": src_name, "dimensions_m": [round(v, 5) for v in (hi-lo)], "collision": "NoCollision", "status": "candidate-only"})
    os.makedirs(LIB, exist_ok=True); os.makedirs(RENDERS, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=False)
    stage, cam = staging(scene)
    stage_floor = bpy.data.objects.get("CW_STANDALONE_THUMB_FLOOR")
    for record in records:
        o = bpy.data.objects[record["name"]]
        # Render the intact module in isolation; otherwise the two masters
        # overlap at their source origin and one hides the other.
        # The library contains many candidate meshes at local origin.  Hide
        # every non-stage mesh, not merely the other standalone modules, so a
        # previously imported detail/floor cannot obscure this validation view.
        for candidate in [x for x in scene.objects if x.type == "MESH"]:
            candidate.hide_render = candidate not in (o, stage_floor)
        max_dim = max(o.dimensions)
        cam.location = (max_dim*2.3, -max_dim*2.8, max_dim*1.7)
        cam.rotation_euler = (Vector((0, 0, max_dim*.45)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(RENDERS, record["name"] + ".png")
        bpy.ops.render.render(write_still=True)
        print("THUMB|" + scene.render.filepath)
    for candidate in [x for x in scene.objects if x.type == "MESH"]:
        candidate.hide_render = False
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"library": "CW_StandaloneModules_v001", "source_files_unchanged": True, "modules": records}, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=False)
    print("LIBRARY_UPDATED|" + BLEND); print("MANIFEST|" + MANIFEST)

if __name__ == "__main__": main()
