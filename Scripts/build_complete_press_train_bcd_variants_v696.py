"""Derive complete, isolated Train B-D successors from the passing Train A v694."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
MAT_ROOT = "/Game/LineBoss/Developer/Validation/PressTrains/CompleteVariants_v696/Materials"
OUT = ROOT / "Saved/Audits/PressTrains/complete_press_train_bcd_variants_build_v696.json"
VARIANTS = {
    "B": {"family": "FLOORS / UNDERBODY", "colour": (0.302, 0.545, 0.290),
          "cue": "DEEP DRAW / HEAVY TRIM-SCRAP"},
    "C": {"family": "CLOSURES", "colour": (0.784, 0.482, 0.176),
          "cue": "MIXED-MODEL / FLEXIBLE GRIPPERS"},
    "D": {"family": "REINFORCEMENTS / SMALL PANELS", "colour": (0.459, 0.341, 0.749),
          "cue": "SMALL DIES / HIGH VARIETY"},
}

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def tag_strings(actor):
    return [str(tag) for tag in actor.tags]

def replace_identity_tags(actor, letter):
    values = []
    for value in tag_strings(actor):
        if value == "LB.PressTrain.Installed.TRAIN_A":
            value = f"LB.PressTrain.Installed.TRAIN_{letter}"
        if value not in values:
            values.append(value)
    values.extend(v for v in (
        f"LB.PressTrain.Train{letter}.CompleteVariant.v696",
        "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    ) if v not in values)
    actor.tags = [unreal.Name(v) for v in values]

def make_material(letter, colour):
    name = f"M_CA_MW_PT_Train{letter}Accent_v696"
    path = f"{MAT_ROOT}/{name}"
    if library.does_asset_exist(path):
        raise RuntimeError(f"Refusing to overwrite {path}")
    material = asset_tools.create_asset(name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -350, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metallic = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 30)
    metallic.set_editor_property("r", 0.32)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 130)
    rough.set_editor_property("r", 0.48)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material

if OUT.exists():
    raise RuntimeError("Refusing to overwrite v696 audit")
if sha(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 changed before variant build")

reports = {}
for letter, spec in VARIANTS.items():
    target = f"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrain{letter}_CompleteVariant_v696"
    if library.does_asset_exist(target):
        raise RuntimeError(f"Refusing to overwrite {target}")
    if not levels.new_level_from_template(target, BASE):
        raise RuntimeError(f"Could not derive Train {letter}")
    actors = list(actors_api.get_all_level_actors())
    authority = [a for a in actors if isinstance(a, unreal.LBPressTrainAStation)]
    if len(authority) != 1:
        raise RuntimeError(f"Train {letter}: authority count {len(authority)}")
    authority = authority[0]
    if not authority.configure_train_variant(unreal.Name(f"TRAIN_{letter}"), f"TRAIN {letter}",
                                             spec["family"], unreal.LinearColor(*spec["colour"], 1.0)):
        raise RuntimeError(f"Train {letter}: native configuration refused")
    authority.set_actor_label(f"CA_MW_PressTrain{letter}_SharedAuthority_v696")
    accent = make_material(letter, spec["colour"])
    accented, cued = [], []
    gripper_index = 0
    for actor in actors:
        replace_identity_tags(actor, letter)
        label = actor.get_actor_label()
        if label.startswith("PTA_"):
            actor.set_actor_label(f"PT{letter}_" + label[4:])
        elif "TrainA" in label:
            actor.set_actor_label(label.replace("TrainA", f"Train{letter}"))
        values = set(tag_strings(actor))
        roles = {v.rsplit(".", 1)[-1] for v in values if v.startswith("LB.PressTrain.Role.")}
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        # Accent only identity/control/tooling pieces; retain yellow safety semantics.
        accent_roles = {"stage_identity", "stage_hmi_screen", "inspection_result_screen",
                        "runtime_hmi_screen", "moving_upper_die", "fixed_lower_die"}
        if comp and roles.intersection(accent_roles):
            comp.set_material(0, accent)
            accented.append(actor.get_actor_label())
        if letter == "B" and roles.intersection({"moving_upper_die", "fixed_lower_die"}) \
                and values.intersection({"LB.PressTrain.Stage.S02", "LB.PressTrain.Stage.S03"}):
            s = actor.get_actor_scale3d()
            actor.set_actor_scale3d(unreal.Vector(s.x * 1.04, s.y * 1.04, s.z * 1.08))
            actor.tags.append(unreal.Name("LB.PressTrain.VariantB.DeepDrawTooling")); cued.append(actor.get_actor_label())
        elif letter == "C" and roles.intersection({"transfer_crossbar", "transfer_gripper"}):
            factor = 1.12 if gripper_index % 2 == 0 else 0.88; gripper_index += 1
            s = actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(s.x * factor, s.y, s.z))
            actor.tags.append(unreal.Name("LB.PressTrain.VariantC.FlexibleMixedModelGripper")); cued.append(actor.get_actor_label())
        elif letter == "D" and roles.intersection({"moving_upper_die", "fixed_lower_die"}):
            s = actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(s.x * .82, s.y * .84, s.z * .90))
            actor.tags.append(unreal.Name("LB.PressTrain.VariantD.SmallerHighVarietyDie")); cued.append(actor.get_actor_label())
    if not levels.save_current_level():
        raise RuntimeError(f"Train {letter}: save failed")
    map_file = ROOT / f"Content/LineBoss/Developer/Validation/PressTrains/LB_PressTrain{letter}_CompleteVariant_v696.umap"
    failures = []
    if not accented: failures.append("no accent actors")
    if not cued: failures.append("no variant tooling cues")
    installed = sum(f"LB.PressTrain.Installed.TRAIN_{letter}" in tag_strings(a) for a in actors)
    stale = sum("LB.PressTrain.Installed.TRAIN_A" in tag_strings(a) for a in actors)
    if installed == 0 or stale: failures.append(f"installed={installed}, stale_A={stale}")
    reports[letter] = {
        "map": target, "map_sha256": sha(map_file), "train_id": f"TRAIN_{letter}",
        "part_family": spec["family"], "variant_cue": spec["cue"], "actor_count": len(actors),
        "installed_scope_actor_count": installed, "accent_actor_count": len(accented),
        "cue_actor_count": len(cued), "p0_separated_actor_count": sum("LB.P0.SeparatedPresentation.v694" in tag_strings(a) for a in actors),
        "failures": failures,
    }
    if failures:
        raise RuntimeError(f"Train {letter}: {'; '.join(failures)}")

if sha(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 changed after variant build")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v696", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__COMPLETE_TRAINS_B_D_DERIVED_WITH_DISTINCT_IDENTITIES__PIE_VISUAL_PENDING",
    "source_map": BASE, "variants": reports, "shared_parent_geometry": True,
    "world_placement_invented": False, "meshy_credits_used": 0,
    "protected_map_sha256": PROTECTED_SHA, "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_PRESS_TRAIN_BCD_VARIANTS_V696_PASS")
