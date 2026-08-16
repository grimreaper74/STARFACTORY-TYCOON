"""Apply dedicated smooth industrial PBR materials and balanced lighting to isolated dock v005."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005"
DEST = "/Game/LineBoss/SupportRobots/ServiceDocks/VisualMaterials_v005"
ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved/Audits/SupportRobots/service_dock_family_unreal_visual_build_v005.json"
V253 = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

SPECS = {
    "Charcoal": ("#202428", 0.57, 0.18, "#000000", 0.0),
    "Graphite": ("#343B3F", 0.50, 0.28, "#000000", 0.0),
    "SafetyYellow": ("#F2C300", 0.46, 0.05, "#000000", 0.0),
    "CairnwellGreen": ("#1F4B44", 0.48, 0.08, "#000000", 0.0),
    "ServiceGrey": ("#666D70", 0.52, 0.12, "#000000", 0.0),
    "MachinedSteel": ("#7F8991", 0.31, 1.0, "#000000", 0.0),
    "Rubber": ("#0A0D10", 0.82, 0.0, "#000000", 0.0),
    "Label": ("#C7CED0", 0.62, 0.0, "#000000", 0.0),
    "EStopRed": ("#B6251E", 0.38, 0.05, "#000000", 0.0),
    "GreenLens": ("#135E31", 0.22, 0.0, "#18C45A", 2.2),
    "AmberLens": ("#A94B0B", 0.24, 0.0, "#FF7A18", 2.0),
    "FluidBlue": ("#16699A", 0.28, 0.18, "#000000", 0.0),
    "WasteOrange": ("#D35A12", 0.43, 0.05, "#000000", 0.0),
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def srgb_hex(value):
    channels = [int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return unreal.LinearColor(*linear, 1.0)


def expression(material, cls, x, y):
    return mel.create_material_expression(material, cls, x, y)


def create_master():
    path = f"{DEST}/M_LB_ServiceDock_SmoothIndustrial_Master_v005"
    if lib.does_asset_exist(path):
        raise RuntimeError(f"Refusing to overwrite {path}")
    material = tools.create_asset("M_LB_ServiceDock_SmoothIndustrial_Master_v005", DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError("Could not create dock material master")
    base = expression(material, unreal.MaterialExpressionVectorParameter, -500, -180)
    base.set_editor_properties({"parameter_name": "BaseColour", "default_value": srgb_hex("#30363A")})
    rough = expression(material, unreal.MaterialExpressionScalarParameter, -500, -20)
    rough.set_editor_properties({"parameter_name": "Roughness", "default_value": 0.52})
    metallic = expression(material, unreal.MaterialExpressionScalarParameter, -500, 120)
    metallic.set_editor_properties({"parameter_name": "Metallic", "default_value": 0.12})
    emissive_colour = expression(material, unreal.MaterialExpressionVectorParameter, -500, 280)
    emissive_colour.set_editor_properties({"parameter_name": "EmissiveColour", "default_value": srgb_hex("#000000")})
    emissive_strength = expression(material, unreal.MaterialExpressionScalarParameter, -500, 420)
    emissive_strength.set_editor_properties({"parameter_name": "EmissiveStrength", "default_value": 0.0})
    emissive = expression(material, unreal.MaterialExpressionMultiply, -220, 320)
    mel.connect_material_expressions(emissive_colour, "", emissive, "A")
    mel.connect_material_expressions(emissive_strength, "", emissive, "B")
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def create_instance(name, parent, spec):
    asset_name = f"MI_LB_ServiceDock_{name}_v005"
    path = f"{DEST}/{asset_name}"
    if lib.does_asset_exist(path):
        raise RuntimeError(f"Refusing to overwrite {path}")
    instance = tools.create_asset(asset_name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if instance is None:
        raise RuntimeError(f"Could not create {path}")
    instance.set_editor_property("parent", parent)
    colour, roughness, metallic, emissive_colour, emissive_strength = spec
    mel.set_material_instance_vector_parameter_value(instance, "BaseColour", srgb_hex(colour))
    mel.set_material_instance_scalar_parameter_value(instance, "Roughness", roughness)
    mel.set_material_instance_scalar_parameter_value(instance, "Metallic", metallic)
    mel.set_material_instance_vector_parameter_value(instance, "EmissiveColour", srgb_hex(emissive_colour))
    mel.set_material_instance_scalar_parameter_value(instance, "EmissiveStrength", emissive_strength)
    mel.update_material_instance(instance)
    lib.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current}, expected {MAP}")
v253_before = sha256(V253)
master = create_master()
materials = {name: create_instance(name, master, spec) for name, spec in SPECS.items()}
floor_material = lib.load_asset("/Game/LineBoss/Candidates/PressShop/PR004ConcreteFloor_v117/Materials/M_CA_MW_PR004_NeutralSealedConcrete_v117")
if not isinstance(floor_material, unreal.MaterialInterface):
    raise RuntimeError("Missing retained sealed concrete material")


def role_for(slot_name):
    name = slot_name.lower()
    if "safetyyellow" in name: return "SafetyYellow"
    if "cairnwellgreen" in name: return "CairnwellGreen"
    if "estopred" in name: return "EStopRed"
    if "greenlens" in name: return "GreenLens"
    if "amberlens" in name or "servicelamp" in name: return "AmberLens"
    if "fluidblue" in name or "cleanwater" in name or "dockwater" in name: return "FluidBlue"
    if "wasteorange" in name or "dockwaste" in name or "recovery" in name: return "WasteOrange"
    if "rubber" in name or "hose" in name or "conduit" in name: return "Rubber"
    if "label" in name: return "Label"
    if "brushedsteel" in name or "toolsteel" in name or "docksteel" in name: return "MachinedSteel"
    if "panel" in name: return "ServiceGrey"
    if "graphite" in name: return "Graphite"
    if "charcoal" in name or "frame" in name: return "Charcoal"
    return None


actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
bindings = []
unmapped = []
for label in ("LB_DOCK_INTAKE_MR01_v005", "LB_DOCK_INTAKE_CR01_v008"):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError(f"Missing dock actor {label}")
    mesh = actor.static_mesh_component.static_mesh
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        role = role_for(slot_name)
        if role is None:
            unmapped.append({"actor": label, "slot": index, "slot_name": slot_name})
            continue
        actor.static_mesh_component.set_material(index, materials[role])
        bindings.append({"actor": label, "slot": index, "slot_name": slot_name, "role": role})
if unmapped:
    raise RuntimeError(f"Unmapped slots: {unmapped}")
floor = actors.get("LB_DOCK_INTAKE_Floor")
floor.static_mesh_component.set_material(0, floor_material)

for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.SkyLight):
        actor.light_component.set_editor_property("intensity", 0.48)
    elif isinstance(actor, unreal.RectLight):
        actor.light_component.set_editor_property("intensity", 950.0 if actor.get_actor_label().endswith("01") else 700.0)
    elif isinstance(actor, unreal.CameraActor):
        component = actor.camera_component
        settings = component.get_editor_property("post_process_settings")
        settings.set_editor_properties({
            "override_auto_exposure_method": True,
            "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
            "override_auto_exposure_min_brightness": True,
            "override_auto_exposure_max_brightness": True,
            "auto_exposure_min_brightness": 1.0,
            "auto_exposure_max_brightness": 1.0,
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": -0.80,
        })
        component.set_editor_property("post_process_settings", settings)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
map_file = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005.umap"
v253_after = sha256(V253)
if v253_before != v253_after:
    raise RuntimeError("Protected v253 changed")
payload = {
    "$schema": "cairnwell/audit/service-dock-family-unreal-visual-build-v005/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DEDICATED_SMOOTH_INDUSTRIAL_PBR_AND_BALANCED_LIGHTING__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "map_sha256": sha256(map_file),
    "material_master": master.get_path_name(),
    "material_instances": {name: asset.get_path_name() for name, asset in materials.items()},
    "binding_count": len(bindings),
    "unmapped_slots": unmapped,
    "lighting": {"skylight_intensity": 0.48, "rect_lights": [950.0, 700.0], "camera_exposure_bias": -0.80},
    "v253_sha256_before": v253_before,
    "v253_sha256_after": v253_after,
    "visual_gate_passed": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_VISUAL_V005_BUILD_PASS bindings={len(bindings)}")
