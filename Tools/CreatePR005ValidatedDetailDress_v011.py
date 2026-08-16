"""Creates a review-only PR005 v011 derivative; the input blend and all Meshy sources remain unchanged."""
import bpy
import math
import os
import sys


library_blend, destination = sys.argv[sys.argv.index("--") + 1:][:2]

source_names = [
    "CW_Detail_Bracket_ServiceLug_L", "CW_Detail_Bracket_ServiceLug_R",
    "CW_Detail_Bumper_CrossRail_A", "CW_Detail_Cable_GlandStrip_A",
    "CW_Detail_Cable_JunctionBlock_A", "CW_Detail_EStop_ControlCap_A",
    "CW_Detail_Handle_Long_A", "CW_Detail_Handle_RecessedTall_A",
    "CW_Detail_Hinge_Long_A", "CW_Detail_Hinge_MicroStrip_A",
    "CW_Detail_Latch_Tall_A", "CW_Detail_ServiceBox_Compact_A",
    "CW_Detail_Vent_FilterFrame_A",
]

with bpy.data.libraries.load(library_blend, link=False) as (data_from, data_to):
    data_to.objects = [name for name in source_names if name in data_from.objects]

collection = bpy.data.collections.get("97_PR005_MESHY_VISUAL_SKIN_V011")
if collection is None:
    collection = bpy.data.collections.new("97_PR005_MESHY_VISUAL_SKIN_V011")
    bpy.context.scene.collection.children.link(collection)

loaded = {obj.name: obj for obj in bpy.data.objects if obj.name in source_names}

def place(source, name, location, rotation=(0, 0, 0), scale=(1, 1, 1), note=""):
    template = loaded[source]
    obj = template.copy()
    obj.data = template.data.copy()
    obj.name = name
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    obj["CW_SourceLibrary"] = "CW_IndustrialDetailLibrary_v001"
    obj["CW_SourceObject"] = source
    obj["CW_UsagePolicy"] = "visual-only review derivative; no functional collision; no pivots; no runtime use"
    obj["CW_PlacementRationale"] = note
    obj.display_type = 'TEXTURED'
    return obj

# Operator-side service bay (negative X): fixed skin only, below roof and clear of the process core.
place("CW_Detail_Hinge_Long_A", "SKIN_PR005_v011_OperatorDoorHinge_A", (-2.955, -4.20, 1.65), note="Operator-side fixed service-bay panel hinge")
place("CW_Detail_Hinge_Long_A", "SKIN_PR005_v011_OperatorDoorHinge_B", (-2.955, -2.92, 1.65), note="Operator-side fixed service-bay panel hinge")
place("CW_Detail_Handle_Long_A", "SKIN_PR005_v011_OperatorDoorHandle_A", (-2.965, -3.48, 1.67), note="Operator-side fixed service-bay door pull")
place("CW_Detail_Latch_Tall_A", "SKIN_PR005_v011_OperatorDoorLatch_A", (-2.985, -3.25, 1.62), note="Operator-side fixed service-bay latch")
place("CW_Detail_Handle_RecessedTall_A", "SKIN_PR005_v011_OperatorDoorHandle_B", (-2.97, -3.88, 1.50), note="Operator-side fixed service-bay recessed pull")
place("CW_Detail_Vent_FilterFrame_A", "SKIN_PR005_v011_OperatorVent_A", (-2.965, -3.72, 2.42), scale=(1.2, 1.6, 1.3), note="Operator-side upper service ventilation")
place("CW_Detail_Vent_FilterFrame_A", "SKIN_PR005_v011_OperatorVent_B", (-2.965, -3.44, 2.42), scale=(1.2, 1.6, 1.3), note="Operator-side upper service ventilation")
place("CW_Detail_ServiceBox_Compact_A", "SKIN_PR005_v011_OperatorServiceBox", (-3.035, -3.66, 1.08), note="Operator-side static service box")
place("CW_Detail_EStop_ControlCap_A", "SKIN_PR005_v011_OperatorEStopHousing", (-3.12, -3.64, 1.10), note="Operator-side static E-stop housing, visual only")

# Utilities side (positive X): fixed service bay only.
place("CW_Detail_Vent_FilterFrame_A", "SKIN_PR005_v011_UtilitiesVent_A", (2.965, -3.82, 2.42), rotation=(0, 0, math.pi), scale=(1.2, 1.6, 1.3), note="Utilities-side upper service ventilation")
place("CW_Detail_Vent_FilterFrame_A", "SKIN_PR005_v011_UtilitiesVent_B", (2.965, -3.54, 2.42), rotation=(0, 0, math.pi), scale=(1.2, 1.6, 1.3), note="Utilities-side upper service ventilation")
place("CW_Detail_Cable_JunctionBlock_A", "SKIN_PR005_v011_UtilitiesJunction", (3.00, -3.34, 1.15), rotation=(0, 0, math.pi), note="Utilities-side static cable junction")
place("CW_Detail_Cable_GlandStrip_A", "SKIN_PR005_v011_UtilitiesGland_A", (3.01, -3.57, 1.16), rotation=(0, 0, math.pi), note="Utilities-side static cable gland")
place("CW_Detail_Cable_GlandStrip_A", "SKIN_PR005_v011_UtilitiesGland_B", (3.01, -3.12, 1.16), rotation=(0, 0, math.pi), note="Utilities-side static cable gland")

# Roof furniture: over the roof skin and away from the moving heads, strip path and service doors.
place("CW_Detail_Bracket_ServiceLug_L", "SKIN_PR005_v011_RoofLug_Operator", (-1.88, 0.82, 3.56), note="Static roof lifting/service lug")
place("CW_Detail_Bracket_ServiceLug_R", "SKIN_PR005_v011_RoofLug_Utilities", (1.88, 0.82, 3.56), rotation=(0, 0, math.pi), note="Static roof lifting/service lug")
place("CW_Detail_Bumper_CrossRail_A", "SKIN_PR005_v011_EntrySafetyRail", (0.0, -5.31, 2.30), note="Entry-surround protective rail above coil/strip interface")

# The imports are visual pieces only. They never receive collision, movement, sockets or export flags.
for obj in collection.objects:
    obj["Collision"] = "NoCollision"
    obj["Functional"] = False
    obj["ExportToRuntime"] = False

# Remove appended templates; only deliberate placement copies remain in the derivative.
for template in loaded.values():
    bpy.data.objects.remove(template, do_unlink=True)

bpy.context.scene["CW_PR005_v011_Status"] = "candidate-only art review derivative"
bpy.context.scene["CW_PR005_v011_Source"] = "PR005_CairnwellMeshySkin_v010.blend + validated small detail library only"
bpy.context.scene["CW_PR005_v011_Constraints"] = "No changes to engineering core, pivots, moving hierarchy, collision, process path, Unreal or v913"
os.makedirs(os.path.dirname(destination), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=destination, check_existing=False)
print("SAVED|{}|pieces={}".format(destination, len(collection.objects)))
