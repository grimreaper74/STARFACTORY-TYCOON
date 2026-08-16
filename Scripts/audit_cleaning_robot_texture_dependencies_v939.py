"""Verify the accepted cleaning-robot visual has self-contained Blender images."""
import bpy, json
from pathlib import Path

out=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopRobots\cleaning_robot_texture_dependencies_v939.json")
out.parent.mkdir(parents=True,exist_ok=True)
images=[]
for img in bpy.data.images:
    if img.name=="Render Result": continue
    images.append({"name":img.name,"source":img.source,"filepath":img.filepath,"packed":bool(img.packed_file),"colorspace":img.colorspace_settings.name,"size":list(img.size)})
missing=[i["name"] for i in images if i["source"]=="FILE" and not i["packed"] and not bpy.path.abspath(i["filepath"])]
payload={"source":bpy.data.filepath,"materials":[m.name for m in bpy.data.materials],"images":images,"image_count":len(images),"all_file_images_packed":all(i["packed"] for i in images if i["source"]=="FILE"),"failures":missing}
out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print("LINE_BOSS_CLEANING_ROBOT_TEXTURE_AUDIT_V939",len(images),payload["all_file_images_packed"],missing)
