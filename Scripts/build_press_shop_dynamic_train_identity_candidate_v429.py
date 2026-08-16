"""Fresh direct-v386 identity: glare-resistant board with the valid native font material."""
from pathlib import Path

source = Path(__file__).with_name("build_press_shop_dynamic_train_identity_candidate_v418.py")
code = source.read_text(encoding="utf-8")
code = code.replace("PhysicalSigns_v411", "PhysicalSigns_v397").replace("_v410", "_v396")
code = code.replace("v418", "v429").replace("V418", "V429")
code = code.replace(
    'yellow=lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredSafetyYellow_v086")',
    'yellow=lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredSafetyYellow_v086"); '
    'charcoal=lib.load_asset("/Game/LineBoss/Candidates/PressShop/TrainIdentity/ReadabilityMaterials_v425/M_CA_MW_IdentityFaceCharcoal_Unlit_v425")'
)
code = code.replace(
    "unreal.TextRenderActor,unreal.Vector(1106,y,850),unreal.Rotator())",
    "unreal.TextRenderActor,unreal.Vector(1106,y,850),unreal.Rotator(yaw=180.0))"
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
