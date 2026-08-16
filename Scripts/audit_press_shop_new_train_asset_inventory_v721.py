"""Read-only inventory of train actors in the mixed review map to identify genuinely new Meshy sources."""
from pathlib import Path
import json, unreal
ROOT=Path(unreal.Paths.project_dir()); MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_MeshyPressVisuals_v717"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_new_train_asset_inventory_v721.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if OUT.exists(): raise RuntimeError("Refusing overwrite v721")
if not levels.load_level(MAP): raise RuntimeError(MAP)
rows=[]
for a in api.get_all_level_actors():
    tags=sorted(str(t) for t in a.tags)
    if not any(t.startswith("LB.PressTrain.Installed.TRAIN_") for t in tags): continue
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    if not c or not c.static_mesh: continue
    rows.append({"label":a.get_actor_label(),"mesh":c.static_mesh.get_path_name(),"transform":{
        "location":list(a.get_actor_location().to_tuple()),"rotation":list(a.get_actor_rotation().to_tuple()),"scale":list(a.get_actor_scale3d().to_tuple())},
        "visible":bool(c.get_editor_property("visible")),"hidden_in_game":bool(c.get_editor_property("hidden_in_game")),"tags":tags})
payload={"revision":"v721","status":"PASS__READ_ONLY_INVENTORY","map":MAP,"actor_count":len(rows),"actors":rows}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_NEW_TRAIN_ASSET_INVENTORY_V721_PASS")
