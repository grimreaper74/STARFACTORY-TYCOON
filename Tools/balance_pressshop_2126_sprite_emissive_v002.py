"""Balance the 2126 sprite cards for the fixed B_stylized Unreal view.

Fully lit cards proved too dark at the management camera, while raw emissive
cards clipped their warm-white detail.  The production compromise is stable
unlit colour at 55 percent strength: source RGB and alpha remain untouched,
but the cards no longer dominate the native environment.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites/"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "balance_sprite_emissive_v002_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.SpriteBalanced.v002")
EXPECTED_UNIQUE_MATERIALS = 12
EMISSIVE_STRENGTH = 0.55
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
    raise RuntimeError("balanced sprite pass already tagged")
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
    raise RuntimeError("expected %d candidate sprite materials, found %d" % (EXPECTED_UNIQUE_MATERIALS, len(materials)))

mel = unreal.MaterialEditingLibrary
balanced = []
for path, material in sorted(materials.items()):
    expressions = list(mel.get_material_expressions(material))
    samples = [expression for expression in expressions if isinstance(expression, unreal.MaterialExpressionTextureSample)]
    if len(samples) != 1:
        raise RuntimeError("expected one texture sample in " + path)
    # This pass is a deliberate supersede of the unsuccessful fully-lit test.
    if not mel.disconnect_material_property(material, unreal.MaterialProperty.MP_BASE_COLOR):
        raise RuntimeError("could not disconnect test base-colour path on " + path)
    multiply = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -120, 0)
    strength = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -320, 180)
    strength.set_editor_property("r", EMISSIVE_STRENGTH)
    if not mel.connect_material_expressions(samples[0], "RGB", multiply, "A"):
        raise RuntimeError("could not connect sprite RGB to multiply on " + path)
    if not mel.connect_material_expressions(strength, "", multiply, "B"):
        raise RuntimeError("could not connect emissive strength on " + path)
    if not mel.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("could not connect balanced emissive on " + path)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mel.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("could not save balanced sprite material " + path)
    balanced.append({"material": path, "actors": users[path], "emissive_strength": EMISSIVE_STRENGTH})

balanced_users = {label for row in balanced for label in row["actors"]}
for actor in actors:
    if actor.get_actor_label() in balanced_users:
        actor.tags = list(actor.tags) + [TAG]
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save balanced sprite map tags")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during balanced sprite pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_SPRITES_BALANCED_UNLIT_055",
    "map": MAP,
    "material_count": len(balanced),
    "emissive_strength": EMISSIVE_STRENGTH,
    "balanced": balanced,
    "supersedes": "fully-lit sprite experiment; source textures and alpha remain unchanged",
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_SPRITE_BALANCE_PASS materials=%d" % len(balanced))
unreal.SystemLibrary.quit_editor()
