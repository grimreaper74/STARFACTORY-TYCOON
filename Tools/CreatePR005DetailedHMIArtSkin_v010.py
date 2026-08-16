"""Create PR005 ArtSkin v010 by adding the detailed v632 Meshy HMI.

This is a non-destructive review derivative.  It copies v009, reads the v632
master without saving it, and does not touch Unreal, v913, or the PR005 v812
engineering authority.  The inherited simple HMI is only hidden in v010.
"""
import bpy, os, shutil
from mathutils import Vector

PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
SOURCE_DIR = os.path.join(PROJECT, "SourceAssets", "Candidate", "PressShop", "PR005", "ArtSkin_v009_MeshyFullSkinColoured")
SOURCE = os.path.join(SOURCE_DIR, "PR005_CairnwellMeshySkin_v009.blend")
OUT_DIR = os.path.join(PROJECT, "SourceAssets", "Candidate", "PressShop", "PR005", "ArtSkin_v010_DetailedHMI")
OUT = os.path.join(OUT_DIR, "PR005_CairnwellMeshySkin_v010.blend")
RENDERS = os.path.join(OUT_DIR, "Renders")
MASTER = os.path.join(PROJECT, "SourceAssets", "Shared", "FactoryAssetLibrary", "MeshyCabinetHMI_v632", "CA_Factory_Cabinet_HMI_MeshyMasters_v632.blend")
MASTER_OBJECT = "SM_CA_Factory_OperatorHMI_MeshyMaster_v632"
PLACEHOLDER = "SM_CA_MW_PR005_HMI_EStop_External_v002"
COLLECTION = "97_PR005_MESHY_VISUAL_SKIN_V010"

def ensure_collection(name):
    collection = bpy.data.collections.get(name)
    if not collection:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection

def move_to_collection(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)

def append_master():
    with bpy.data.libraries.load(MASTER, link=False) as (from_data, to_data):
        if MASTER_OBJECT not in from_data.objects:
            raise RuntimeError("Detailed HMI object missing from v632 master")
        to_data.objects = [MASTER_OBJECT]
    return to_data.objects[0]

def ensure_stage_camera(scene):
    camera = scene.camera
    if not camera:
        raise RuntimeError("v009 review camera missing")
    return camera

def render(scene, camera, filepath, location, target, lens=50):
    camera.location = location
    camera.data.lens = lens
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    print("RENDER|" + filepath)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)
    shutil.copy2(SOURCE, OUT)
    bpy.ops.wm.open_mainfile(filepath=OUT)
    scene = bpy.context.scene
    skin_collection = ensure_collection(COLLECTION)

    placeholder = bpy.data.objects.get(PLACEHOLDER)
    if not placeholder:
        raise RuntimeError("Expected inherited PR005 HMI placeholder missing")
    # Preserve the inherited object as traceable review evidence but exclude it
    # from v010 renders.  Its original movement/collision behaviour is untouched.
    placeholder.hide_render = True
    placeholder.hide_viewport = True
    placeholder["V010ReviewStatus"] = "hidden; superseded visually by detailed v632 HMI only"

    detailed = bpy.data.objects.get("SKIN_PR005_DetailedHMI_v632")
    if not detailed:
        source_object = append_master()
        detailed = source_object.copy()
        detailed.data = source_object.data.copy()
        bpy.data.objects.remove(source_object, do_unlink=True)
        detailed.name = "SKIN_PR005_DetailedHMI_v632"
        detailed.data.name = "SKIN_PR005_DetailedHMI_v632_Mesh"
        skin_collection.objects.link(detailed)
        # The v632 master is a floor-seated complete HMI.  Its detail stays
        # unscaled; we rotate and place it at the existing operator interface.
        detailed.location = (-2.41, 3.0, 0.0)
        detailed.rotation_euler = (0.0, 0.0, 0.0)
        detailed["FamilyId"] = "PR005_VisualSkin"
        detailed["Role"] = "Detailed operator HMI visual replacement"
        detailed["SourceModel"] = MASTER
        detailed["SourceObject"] = MASTER_OBJECT
        detailed["CollisionPolicy"] = "NoCollision"
        detailed["RuntimeStatus"] = "CANDIDATE_ART_REVIEW_ONLY"
        detailed["FunctionalBinding"] = "None: visual-only review derivative"
        detailed["PlacementAuthority"] = "Inherited PR005 HMI visual interface position"
        detailed["LightInterface"] = "Reserve existing station-state signal-light binding for later Unreal validation; no Blender functional claim"

    scene["ArtSkinVersion"] = "v010 Detailed Meshy HMI review derivative"
    scene["SourceImmutability"] = "PR005 v812 and v632 master read-only; no Unreal or v913 changes"
    scene["ArtReviewStatus"] = "candidate-only; not imported or approved"
    bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False)

    camera = ensure_stage_camera(scene)
    # Render a useful close operator review plus a compatible three-quarter.
    render(scene, camera, os.path.join(RENDERS, "01_PR005_v010_DetailedHMI_OperatorDetail.png"),
           (-8.8, -5.0, 4.7), (-2.25, 2.9, 1.3), 58)
    render(scene, camera, os.path.join(RENDERS, "02_PR005_v010_DetailedHMI_ThreeQuarter.png"),
           (-11.5, -13.5, 8.2), (0.0, 1.8, 1.6), 52)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False)
    print("DERIVATIVE|" + OUT)
    print("SOURCE_MASTERS_UNCHANGED|" + SOURCE + "|" + MASTER)

if __name__ == "__main__":
    main()
