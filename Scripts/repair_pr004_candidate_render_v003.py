"""Repair PR-004 candidate-only materials, lighting and fixed-camera sightlines.

This deliberately edits only the isolated Candidate_v002 assets/map.  It does
not promote any module or claim release quality.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002"
ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v002"
MAT_ROOT = ROOT + "/MaterialsDirect_v003"
IMPORT_AUDIT = REPO / "Saved/Audits/pr004_unreal_import_candidate_v002.json"
OUT = REPO / "Saved/Audits/pr004_candidate_render_repair_v003.json"

SPECS = {
    "MachineDark": ((0.025, 0.032, 0.040), 0.72, 0.62, False),
    "SafetyYellow": ((0.82, 0.42, 0.025), 0.18, 0.48, False),
    "MaintenanceOrange": ((0.76, 0.20, 0.018), 0.12, 0.50, False),
    "MachinedSteel": ((0.42, 0.46, 0.49), 0.92, 0.24, False),
    "CastIron": ((0.055, 0.063, 0.070), 0.72, 0.78, False),
    "Rubber": ((0.008, 0.010, 0.012), 0.00, 0.84, False),
    "HoseCable": ((0.012, 0.016, 0.020), 0.02, 0.72, False),
    "SensorBlue": ((0.010, 0.16, 0.34), 0.18, 0.26, False),
    "OpaqueSensorLens": ((0.018, 0.10, 0.16), 0.26, 0.16, False),
    "WarningRed": ((0.55, 0.008, 0.004), 0.08, 0.34, False),
    "ReadyGreen": ((0.010, 0.34, 0.070), 0.06, 0.30, False),
    "ServiceLabel": ((0.62, 0.64, 0.61), 0.10, 0.58, False),
    "GreaseResidue": ((0.045, 0.032, 0.014), 0.02, 0.32, False),
    "CoilSteel": ((0.29, 0.32, 0.34), 0.94, 0.31, False),
    "CoilPackaging": ((0.16, 0.18, 0.19), 0.04, 0.66, True),
    "BandSteel": ((0.22, 0.24, 0.25), 0.91, 0.29, True),
    "DullGreyWrap": ((0.34, 0.36, 0.37), 0.02, 0.78, True),
    "RemovedFilm": ((0.032, 0.040, 0.045), 0.00, 0.76, True),
    "CompactedFilm": ((0.018, 0.024, 0.028), 0.00, 0.88, True),
    "EdgeProtector": ((0.22, 0.14, 0.070), 0.00, 0.86, True),
    "IdentityLabel": ((0.62, 0.60, 0.52), 0.00, 0.68, True),
    "ValidationConcrete": ((0.105, 0.105, 0.095), 0.02, 0.88, False),
    "BackdropFloor": ((0.055, 0.060, 0.064), 0.02, 0.92, False),
}

assets = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def create_direct(name: str, spec):
    colour, metallic, roughness, two_sided = spec
    asset_name = f"M_LB_PR004_{name}_Direct_v003"
    path = f"{MAT_ROOT}/{asset_name}"
    material = assets.load_asset(path) if assets.does_asset_exist(path) else None
    if material is None:
        material = tools.create_asset(asset_name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_properties({
        "blend_mode": unreal.BlendMode.BLEND_OPAQUE,
        "two_sided": two_sided,
    })
    if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -420, -80
    )
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 50
    )
    metal.set_editor_property("r", metallic)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 160
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    assets.save_loaded_asset(material, only_if_is_dirty=False)
    return material


direct = {name: create_direct(name, spec) for name, spec in SPECS.items()}
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

source_audit = json.loads(IMPORT_AUDIT.read_text(encoding="utf-8"))
mesh_records = []
for record in source_audit["imported_assets"]:
    mesh = assets.load_asset(record["asset"])
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing candidate mesh {record['asset']}")
    changes = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        current = slot.get_editor_property("material_interface")
        current_name = current.get_name() if current is not None else ""
        if not current_name.startswith("MI_LB_PR004_"):
            continue
        key = current_name.removeprefix("MI_LB_PR004_")
        if key not in direct:
            raise RuntimeError(f"No direct material replacement for {current_name}")
        mesh.set_material(index, direct[key])
        changes.append({"slot": index, "from": current_name, "to": direct[key].get_name()})
    assets.save_loaded_asset(mesh, only_if_is_dirty=False)
    mesh_records.append({"asset": mesh.get_path_name(), "rebindings": changes})

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

all_actors = list(actors.get_all_level_actors())
actor_by_label = {actor.get_actor_label(): actor for actor in all_actors}
candidate_tag = unreal.Name("LB.PR004.ImportCandidate.Candidate_v002")

component_rebindings = []
for actor in all_actors:
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        current_name = current.get_name() if current is not None else ""
        if not current_name.startswith("MI_LB_PR004_"):
            continue
        key = current_name.removeprefix("MI_LB_PR004_")
        if key not in direct:
            continue
        component.set_material(index, direct[key])
        component_rebindings.append({"actor": actor.get_actor_label(), "slot": index, "to": direct[key].get_name()})

# Remove only candidate-map validation lamps/lights which obstructed the fixed
# review cameras.  No source or vendor asset is deleted.
remove_labels = {
    "LB_PR004_ValidationKey", "LB_PR004_ValidationFill", "LB_PR004_ValidationAmbient",
    "LB_PR004_FixedExposure", "LB_PR004_VENDOR_Lamp_NW", "LB_PR004_VENDOR_Lamp_SE",
    "LB_PR004_ValidationFloorExtension_v003", "LB_PR004_ValidationBackdrop_N_v003",
    "LB_PR004_ValidationBackdrop_W_v003",
}
removed = []
for label in remove_labels:
    actor = actor_by_label.get(label)
    if actor is not None:
        actors.destroy_actor(actor)
        removed.append(label)


def tags(*values: str):
    return [candidate_tag, unreal.Name("LB.Asset.Candidate.NotPromoted"), *(unreal.Name(value) for value in values)]


def spawn_cube(label, location, size, material):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_editor_properties({"cast_shadow": False, "mobility": unreal.ComponentMobility.STATIC})
    actor.set_editor_property("tags", tags("LB.Asset.ValidationOnly", "LB.Environment.Validation"))
    return actor


# A larger floor and low backdrops replace the black void without obscuring the
# cameras outside the locked 12.4 x 14.4 m cell envelope.
spawn_cube("LB_PR004_ValidationFloorExtension_v003", (0, 0, -18), (3200, 3200, 20), direct["BackdropFloor"])
spawn_cube("LB_PR004_ValidationBackdrop_N_v003", (0, 1500, 180), (3200, 20, 360), direct["MachineDark"])
spawn_cube("LB_PR004_ValidationBackdrop_W_v003", (-1500, 0, 180), (20, 3200, 360), direct["MachineDark"])

# Four broad, shadowless industrial fixtures plus a cool fill avoid both Lumen
# speckle and clipped white highlights.  These are deterministic review lights,
# not release lighting.
light_specs = (
    ("LB_PR004_ValidationCeiling_NW_v003", (-360, 380, 650), (0, 120, 110), 480.0, unreal.Color(255, 238, 214, 255)),
    ("LB_PR004_ValidationCeiling_NE_v003", (360, 380, 650), (180, 120, 110), 460.0, unreal.Color(240, 246, 255, 255)),
    ("LB_PR004_ValidationCeiling_SW_v003", (-360, -380, 650), (-160, -80, 100), 420.0, unreal.Color(230, 240, 255, 255)),
    ("LB_PR004_ValidationCeiling_SE_v003", (360, -380, 650), (180, -60, 100), 400.0, unreal.Color(255, 232, 205, 255)),
)
lights = []
for label, location, target, intensity, colour in light_specs:
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(label)
    light.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(*target)), False
    )
    light.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 1500.0,
        "source_width": 420.0,
        "source_height": 260.0,
        "light_color": colour,
        "cast_shadows": False,
        "affect_global_illumination": False,
        "affect_reflection": True,
    })
    light.set_editor_property("tags", tags("LB.Light.Validation"))
    lights.append(label)

fill = actors.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(0, 0, 700), unreal.Rotator(-52.0, 132.0, 0.0)
)
fill.set_actor_label("LB_PR004_ValidationDirectionalFill_v003")
fill.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 0.28,
    "light_color": unreal.Color(190, 210, 235, 255),
    "cast_shadows": False,
    "affect_global_illumination": False,
})
fill.set_editor_property("tags", tags("LB.Light.Validation"))
lights.append(fill.get_actor_label())

exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label("LB_PR004_FixedExposure_v003")
exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0, "tags": tags("LB.Light.Validation")})
settings = exposure.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.0,
    "override_color_saturation": True,
    "color_saturation": unreal.Vector4(1.03, 1.03, 1.03, 1.0),
})
exposure.set_editor_property("settings", settings)

# Preserve the six established camera names.  Only the film-process view is
# raised above the guard so the machine, film path and compactor are legible.
film_camera = actor_by_label.get("LB_PR004_CAM_FilmDewrap")
if film_camera is not None:
    film_location = unreal.Vector(880.0, 700.0, 690.0)
    film_target = unreal.Vector(300.0, 250.0, 115.0)
    film_camera.set_actor_location(film_location, False, False)
    film_camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(film_location, film_target), False)
    film_camera.get_editor_property("camera_component").set_editor_property("field_of_view", 45.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving repaired PR-004 candidate validation map")
assets.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-candidate-render-repair/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_RENDER_REPAIRED__FRESH_VISUAL_GATE_REQUIRED",
    "map": MAP,
    "promotion_supported": False,
    "direct_material_root": MAT_ROOT,
    "direct_material_count": len(direct),
    "mesh_count_rebound": len(mesh_records),
    "mesh_rebindings": mesh_records,
    "component_override_rebindings": component_rebindings,
    "removed_obstructing_validation_actors": removed,
    "validation_lights": lights,
    "post_process": "manual exposure 0.0; saturation 1.03",
    "film_camera_reframed": film_camera is not None,
    "remaining_gate": "Capture and inspect fresh fixed-camera Unreal screenshots against Pro references.",
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_RENDER_REPAIR_V003={OUT}")
