import bpy

for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.name.startswith("CW_Detail_"):
        print("DETAIL|{}|dims={}|loc={}|rot={}|materials={}".format(
            obj.name,
            tuple(round(value, 4) for value in obj.dimensions),
            tuple(round(value, 4) for value in obj.location),
            tuple(round(value, 4) for value in obj.rotation_euler),
            [slot.material.name if slot.material else None for slot in obj.material_slots],
        ))
