"""Convert the twelve FullHall sprite materials from emissive to Default Lit.

PNG colour and alpha remain unchanged.  Only the lighting path changes so the
machines participate in the approved Unreal B_stylized rig instead of glowing
independently of it.  Candidate-local sprite materials are the only assets
eligible for mutation.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites/"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "convert_sprites_to_lit_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.SpriteLit.v001")
EXPECTED_UNIQUE_MATERIALS = 12
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("sprite-lit pass already tagged in map")

materials = {}
users = {}
for actor in actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        if not isinstance(material, unreal.Material):
            continue
        path = material.get_path_name().split(".")[0]
        if path.startswith(ROOT) and "UnlitMasked" in path:
            materials[path] = material
            users.setdefault(path, []).append(actor.get_actor_label())

if len(materials) != EXPECTED_UNIQUE_MATERIALS:
    raise RuntimeError("expected %d candidate sprite materials, found %d: %s" % (
        EXPECTED_UNIQUE_MATERIALS, len(materials), sorted(materials)))

mel = unreal.MaterialEditingLibrary
converted = []
for path, material in sorted(materials.items()):
    expressions = list(mel.get_material_expressions(material))
    samples = [expression for expression in expressions if isinstance(expression, unreal.MaterialExpressionTextureSample)]
    if len(samples) != 1:
        raise RuntimeError("expected one texture sample in %s, found %d" % (path, len(samples)))
    sample = samples[0]
    if not mel.disconnect_material_property(material, unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("could not disconnect emissive output on " + path)
    if not mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR):
        raise RuntimeError("could not connect base colour on " + path)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mel.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("could not save converted material " + path)
    converted.append({"material": path, "actors": users[path], "texture_sample_count": len(samples)})

for actor in actors:
    if any(actor.get_actor_label() in row["actors"] for row in converted):
        actor.tags = list(actor.tags) + [TAG]

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save sprite-lit map tags")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during sprite material conversion")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_SPRITES_USE_DEFAULT_LIT_BASE_COLOR",
    "map": MAP,
    "converted_material_count": len(converted),
    "converted": converted,
    "preserved": ["source textures", "sRGB", "masked alpha", "two-sided cards", "fixed camera angle"],
    "changed": "texture RGB moved from emissive to Default Lit base colour",
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_SPRITE_LIT_PASS materials=%d" % len(converted))
unreal.SystemLibrary.quit_editor()
