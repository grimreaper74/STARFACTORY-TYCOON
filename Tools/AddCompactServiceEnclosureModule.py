"""Append one visually reviewed compact Meshy service enclosure to the library.

The source blend is read-only.  The copied candidate remains a complete visual
module with NoCollision; it is not an Unreal asset and is not applied to PR005.
"""
import bpy, json, os
from mathutils import Vector

PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
LIB = os.path.join(PROJECT, "SourceAssets", "Shared", "CairnwellIndustrialDetailLibrary_v001")
BLEND = os.path.join(LIB, "CW_IndustrialDetailLibrary_v001.blend")
MANIFEST = os.path.join(LIB, "compact_service_module_manifest_v001.json")
SOURCE = r"C:\Users\greg_\Downloads\Meshy_AI_Compact_industrial_pl_0810151315_generate.blend"
SOURCE_OBJECT = "Meshy_AI_Compact_industrial_pl_0810151315_generate"
TARGET = "CW_Module_CompactServiceEnclosure_Meshy_v081015"

def collection(name):
    result = bpy.data.collections.get(name)
    if not result:
        result = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(result)
    return result

def append_master():
    with bpy.data.libraries.load(SOURCE, link=False) as (from_data, to_data):
        mesh_names = [name for name in from_data.objects if name]
        if SOURCE_OBJECT in mesh_names:
            to_data.objects = [SOURCE_OBJECT]
        else:
            # Retained generate masters sometimes retain a generic object name;
            # accept exactly one mesh source, otherwise fail safely.
            candidates = [name for name in mesh_names if name]
            if len(candidates) != 1:
                raise RuntimeError("Ambiguous source objects: " + repr(candidates))
            to_data.objects = candidates
    result = to_data.objects[0]
    if not result or result.type != "MESH":
        raise RuntimeError("Expected one Meshy mesh in source")
    return result

def bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    lo = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    hi = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return lo, hi

def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    obj = bpy.data.objects.get(TARGET)
    if not obj:
        source = append_master()
        obj = source.copy()
        obj.data = source.data.copy()
        bpy.data.objects.remove(source, do_unlink=True)
        obj.name = TARGET
        obj.data.name = TARGET + "_Mesh"
        collection("CW_StandaloneModules_v001").objects.link(obj)
        lo, hi = bounds(obj)
        floor_centre = Vector(((lo.x + hi.x) * .5, (lo.y + hi.y) * .5, lo.z))
        obj.matrix_world.translation -= floor_centre
        obj["LocalOrigin"] = "bottom centre"
    lo, hi = bounds(obj)
    obj["FamilyId"] = "CW_StandaloneIndustrialModule"
    obj["Role"] = "Vented compact service/cooling enclosure"
    obj["SourceModel"] = SOURCE
    obj["SourceObject"] = SOURCE_OBJECT
    obj["CollisionPolicy"] = "NoCollision"
    obj["RuntimeStatus"] = "SOURCE_REUSABLE_CANDIDATE_ONLY"
    obj["ReuseRule"] = "Keep intact; use only after role-fit review as non-functional visual service enclosure."
    record = {
        "name": TARGET,
        "role": obj["Role"],
        "source_model": SOURCE,
        "source_object": SOURCE_OBJECT,
        "dimensions_m": [round(value, 5) for value in hi - lo],
        "collision": "NoCollision",
        "status": "candidate-only",
        "review_evidence": "Saved/ValidationScreenshots/IndustrialDetailLibrary_Intake/StandaloneMasters/Standalone_CompactPlant.png"
    }
    with open(MANIFEST, "w", encoding="utf-8") as handle:
        json.dump({"source_files_unchanged": True, "module": record}, handle, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=False)
    print("LIBRARY_UPDATED|" + BLEND)
    print("MODULE|" + json.dumps(record))

if __name__ == "__main__":
    main()
