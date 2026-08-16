"""Create isolated Train B-D variants from retained Train A v027 without inventing world placement."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
parent_map = "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027"
parent_file = root / "Content/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027.umap"
expected_parent = "00225848C15668BE523F181FD81A8C1FB472675A724B72847B9E206A7C99848F"
protected_v213 = root / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap"
expected_v213 = "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554"
material_root = "/Game/LineBoss/Candidates/PressTrains/Variants/Candidate_v001/Materials"

variants = {
    "B": {
        "map": "/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001",
        "display": "TRAIN B", "family": "FLOORS / UNDERBODY",
        "accent": (0.302, 0.545, 0.290), "cue": "DEEP-DRAW TOOLING / HEAVY TRIM-SCRAP EXTRACTION",
    },
    "C": {
        "map": "/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001",
        "display": "TRAIN C", "family": "CLOSURES",
        "accent": (0.784, 0.471, 0.176), "cue": "MIXED-MODEL CHANGE / FLEXIBLE GRIPPERS",
    },
    "D": {
        "map": "/Game/LineBoss/Maps/LB_PressTrainDIsolatedVariantCandidate_v001",
        "display": "TRAIN D", "family": "REINFORCEMENTS / SMALL PANELS",
        "accent": (0.459, 0.341, 0.561), "cue": "SMALLER DIES / HIGH-VARIETY CHANGEOVER",
    },
}

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def tags(actor): return {str(tag) for tag in actor.tags}
def add_tags(actor, *values):
    current = list(tags(actor))
    for value in values:
        if value not in current: current.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in sorted(current)])

def surface(letter, colour):
    name = f"M_CA_MW_PT_Train{letter}Accent_v001"
    path = f"{material_root}/{name}"
    if library.does_asset_exist(path):
        return library.load_asset(path)
    material = tools.create_asset(name, material_root, unreal.Material, unreal.MaterialFactoryNew())
    if material is None: raise RuntimeError(f"Could not create {path}")
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -350, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metallic = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 20)
    metallic.set_editor_property("r", 0.34)
    roughness = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 115)
    roughness.set_editor_property("r", 0.56)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material

if sha(parent_file) != expected_parent: raise RuntimeError("Retained v027 changed")
if sha(protected_v213) != expected_v213: raise RuntimeError("Protected v213 changed before variant work")

reports = {}
for letter, spec in variants.items():
    target_map = spec["map"]
    target_file = root / f"Content/LineBoss/Maps/{target_map.rsplit('/', 1)[-1]}.umap"
    out = root / f"Saved/Audits/PressTrains/press_train_{letter.lower()}_isolated_variant_build_v001.json"
    if library.does_asset_exist(target_map) or target_file.exists() or out.exists():
        raise RuntimeError(f"Refusing to overwrite preserved Train {letter} v001")
    if not levels.new_level_from_template(target_map, parent_map):
        raise RuntimeError(f"Could not create Train {letter} from retained v027")
    actors = list(actors_api.get_all_level_actors())
    authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
    if len(authorities) != 1: raise RuntimeError(f"Train {letter}: expected one shared authority")
    authority = authorities[0]
    if not authority.configure_train_variant(
            unreal.Name(f"TRAIN_{letter}"), spec["display"], spec["family"], unreal.LinearColor(*spec["accent"], 1.0)):
        raise RuntimeError(f"Train {letter}: native identity configuration refused")
    authority.set_actor_label(f"CA_MW_PressTrain{letter}_SharedAuthority_v001")
    add_tags(authority, f"LB.PressTrain.Train{letter}.IsolatedVariant.v001",
             "LB.PressTrain.SharedRuntimeAuthority.v001", "LB.Asset.Candidate.v001",
             "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented")

    accent = surface(letter, spec["accent"])
    accent_overrides = []
    cue_rows = []
    hmi_rows = []
    for actor in actors:
        values = tags(actor)
        roles = {value.rsplit(".", 1)[-1] for value in values if value.startswith("LB.PressTrain.Role.")}
        label = actor.get_actor_label()
        if label.startswith("PTA_"): actor.set_actor_label(f"PT{letter}_" + label[4:])
        elif "TrainA" in label: actor.set_actor_label(label.replace("TrainA", f"Train{letter}"))
        add_tags(actor, f"LB.PressTrain.Train{letter}.IsolatedVariant.v001")

        base_accent_roles = {"stage_identity", "stage_hmi_screen", "inspection_result_screen", "runtime_hmi_screen"}
        variant_roles = set()
        if letter == "B":
            variant_roles = {"loaded_outer_panel_die", "moving_upper_die", "fixed_lower_die",
                             "trim_underfloor_scrap_chute", "trim_scrap_extractor", "trim_scrap_bin"}
        elif letter == "C":
            variant_roles = {"transfer_gripper"}
        elif letter == "D":
            variant_roles = {"loaded_outer_panel_die", "moving_upper_die", "fixed_lower_die"}
        if isinstance(actor, unreal.StaticMeshActor) and roles.intersection(base_accent_roles | variant_roles):
            actor.static_mesh_component.set_material(0, accent)
            accent_overrides.append(actor.get_actor_label())

        if letter == "B" and roles.intersection({"moving_upper_die", "fixed_lower_die"}) \
                and ("LB.PressTrain.Stage.S02" in values or "LB.PressTrain.Stage.S03" in values):
            scale = actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(scale.x * 1.04, scale.y * 1.04, scale.z * 1.08))
            add_tags(actor, "LB.PressTrain.VariantB.DeepDrawTooling")
            cue_rows.append(actor.get_actor_label())
        if letter == "B" and roles.intersection({"trim_underfloor_scrap_chute", "trim_scrap_extractor", "trim_scrap_bin"}):
            scale = actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(scale.x * 1.08, scale.y * 1.12, scale.z * 1.08))
            add_tags(actor, "LB.PressTrain.VariantB.HeavyTrimScrapExtraction")
            cue_rows.append(actor.get_actor_label())
        if letter == "C" and "transfer_gripper" in roles:
            factor = 1.14 if len(cue_rows) % 2 == 0 else 0.86
            scale = actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(scale.x * factor, scale.y, scale.z))
            add_tags(actor, "LB.PressTrain.VariantC.FlexibleMixedModelGripper")
            cue_rows.append(actor.get_actor_label())
        if letter == "D" and roles.intersection({"loaded_outer_panel_die", "moving_upper_die", "fixed_lower_die"}):
            scale = actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(scale.x * 0.82, scale.y * 0.84, scale.z * 0.90))
            add_tags(actor, "LB.PressTrain.VariantD.SmallerHighVarietyDie")
            cue_rows.append(actor.get_actor_label())

        if isinstance(actor, unreal.TextRenderActor) and "LB.HMI.PressTrainA.LiveState" in values:
            add_tags(actor, "LB.HMI.PressTrain.LiveState", f"LB.HMI.PressTrain{letter}.LiveState")
            actor.text_render.set_text(
                f"{spec['display']} | ISOLATED\n{spec['family']}\n{spec['cue']}\nWORLD DATUM TBC")
            actor.text_render.set_text_render_color(unreal.Color(
                int(spec["accent"][0] * 255), int(spec["accent"][1] * 255), int(spec["accent"][2] * 255), 255))
            hmi_rows.append(actor.get_actor_label())

    if not levels.save_current_level(): raise RuntimeError(f"Train {letter}: save failed")
    if not target_file.exists(): raise RuntimeError(f"Train {letter}: map package missing")
    failures = []
    if len(actors) != 366: failures.append(f"actor count changed from 366: {len(actors)}")
    if not accent_overrides: failures.append("no visible accent overrides")
    if not cue_rows: failures.append("no variant-specific tooling cues")
    if len(hmi_rows) != 1: failures.append(f"live HMI count {len(hmi_rows)}")
    if str(authority.get_hmi_status().train_id) != f"TRAIN_{letter}": failures.append("native HMI identity mismatch")
    if authority.get_part_family() != spec["family"]: failures.append("native part family mismatch")
    report = {
        "$schema": f"cairnwell/audit/press-train-{letter.lower()}-isolated-variant-build-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": f"PASS__TRAIN_{letter}_ISOLATED_SHARED_RUNTIME_VARIANT_WITH_DISTINCT_IDENTITY_TOOLING_AND_ACCENT__PIE_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
                  if not failures else f"FAIL__TRAIN_{letter}_ISOLATED_VARIANT_BUILD__NOT_PROMOTED",
        "parent_map": parent_map, "parent_sha256": expected_parent,
        "target_map": target_map, "target_sha256": sha(target_file),
        "train_id": f"TRAIN_{letter}", "part_family": spec["family"], "variant_cue": spec["cue"],
        "world_placement": "TBC_NOT_INVENTED", "actor_count": len(actors),
        "accent_override_count": len(accent_overrides), "variant_cue_actor_count": len(set(cue_rows)),
        "live_hmi": hmi_rows, "failures": failures,
        "production_map_changed": False, "promotion_authorized": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    reports[letter] = report
    if failures: raise RuntimeError(f"Train {letter}: {'; '.join(failures)}")

if sha(parent_file) != expected_parent: raise RuntimeError("Retained v027 changed after variant work")
if sha(protected_v213) != expected_v213: raise RuntimeError("Protected v213 changed after variant work")
print(json.dumps({letter: {"status": row["status"], "hash": row["target_sha256"]}
                  for letter, row in reports.items()}, indent=2))
