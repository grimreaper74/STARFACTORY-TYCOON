"""Read-only transform and visibility audit for v002 capture diagnosis."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_camera_light_state.json"
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002")
rows=[]
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label=actor.get_actor_label()
    if not (label.startswith("CAM v002") or label.startswith("B_stylized") or "task light" in label or label.startswith("MESHY v002")):
        continue
    loc=actor.get_actor_location(); rot=actor.get_actor_rotation()
    row={"label":label,"class":actor.get_class().get_name(),"location":[loc.x,loc.y,loc.z],"rotation":[rot.pitch,rot.yaw,rot.roll]}
    if isinstance(actor, unreal.StaticMeshActor):
        row["visible"]=actor.static_mesh_component.is_visible()
        scale=actor.get_actor_scale3d()
        row["scale"]=[scale.x,scale.y,scale.z]
    if isinstance(actor, unreal.Light):
        row["intensity"]=actor.light_component.intensity
    rows.append(row)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status":"PASS__READ_ONLY","rows":rows},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_CAMERA_LIGHT_AUDIT_PASS")
