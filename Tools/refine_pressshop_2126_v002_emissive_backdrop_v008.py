"""Give the roofless v002 press line a stable, non-black rear elevation.

This is an architectural light surface, not a roof and not a new dynamic light.
It is deliberately broad and simple so the actual Meshy press silhouettes read
against it at screenshot distance without more Lumen lights after v005's fault.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED=PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
ROOT="/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
REPORT=PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_emissive_backdrop_v008.json"
TAG=unreal.Name("LB.PressShop.2126.v002.EmissiveBackdrop.v008")

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def make_emissive(name,color,emission):
    path=ROOT+"/"+name
    material=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT,unreal.Material,unreal.MaterialFactoryNew())
    if not isinstance(material,unreal.Material):
        raise RuntimeError("Could not create backdrop material")
    mel=unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base=mel.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-400,-80)
    base.set_editor_property("constant",unreal.LinearColor(*color,1.0))
    rough=mel.create_material_expression(material,unreal.MaterialExpressionConstant,-400,30)
    rough.set_editor_property("r",0.70)
    gain=mel.create_material_expression(material,unreal.MaterialExpressionConstant,-400,-180)
    gain.set_editor_property("r",emission)
    product=mel.create_material_expression(material,unreal.MaterialExpressionMultiply,-160,-80)
    mel.connect_material_expressions(base,"",product,"A")
    mel.connect_material_expressions(gain,"",product,"B")
    mel.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(product,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    return material

if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before=digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002")
actors={actor.get_actor_label():actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v008 already ran")

warm=make_emissive("M_LB_PS2126v002_ArchitecturalWarmWhiteGlow",(0.78,0.75,0.67),0.32)
green=make_emissive("M_LB_PS2126v002_ArchitecturalCairnwellGlow",(0.018,0.11,0.075),0.45)
for label,material in (
    ("2126 v002 | warm-white rear elevation",warm),
    ("2126 v002 | Cairnwell supervision ribbon",green),
):
    actor=actors.get(label)
    if not isinstance(actor,unreal.StaticMeshActor):
        raise RuntimeError("Missing backdrop actor "+label)
    actor.static_mesh_component.set_material(0,material)
    actor.tags=list(actor.tags)+[TAG,unreal.Name("LB.Architecture.EmissiveLightSurface")]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v008")
after=digest(PROTECTED)
if before!=after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({
    "status":"PASS__ROOFLESS_EMISSIVE_ARCHITECTURAL_BACKDROP_APPLIED",
    "candidate_map":MAP,
    "dynamic_lights_added":0,
    "roof_created":False,
    "backdrop_materials":{"warm_white":warm.get_path_name(),"cairnwell":green.get_path_name()},
    "protected_v438_sha256_before":before,
    "protected_v438_sha256_after":after,
},indent=2),encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_EMISSIVE_BACKDROP_V008_PASS")
