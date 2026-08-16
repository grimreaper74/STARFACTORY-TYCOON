"""Correct v103 stack-ID CCTV legibility and add an exact-map verification camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v103/stack_id_legibility_correction_v103.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())
texts = [actor for actor in actors if isinstance(actor, unreal.TextRenderActor) and "LB.PR010.StackPositionID.v103" in {str(tag) for tag in actor.tags}]
plates = [actor for actor in actors if "LB.PR010.StackIdentityPlate" in {str(tag) for tag in actor.tags}]
reverse_by_value = {
    str(actor.text_render.get_editor_property("text")): actor
    for actor in actors
    if isinstance(actor, unreal.TextRenderActor) and "LB.PR010.StackPositionID.Reverse.v103" in {str(tag) for tag in actor.tags}
}
legacy_by_value = {
    str(actor.text_render.get_editor_property("text")): actor
    for actor in actors
    if isinstance(actor, unreal.TextRenderActor) and "LB.PR010.LegacyStackID.Hidden.v103" in {str(tag) for tag in actor.tags}
}
stacks = [
    actor for actor in actors
    if "identified_blank_stack" in {str(tag) for tag in actor.tags}
    or "quality_hold_stack" in {str(tag) for tag in actor.tags}
]


def stack_for(value):
    legacy = legacy_by_value.get(value)
    if legacy is None or not stacks:
        return None
    expected_x = legacy.get_actor_location().x + 86.0
    expected_y = legacy.get_actor_location().y
    return min(stacks, key=lambda actor: abs(actor.get_actor_location().x - expected_x) + abs(actor.get_actor_location().y - expected_y))


failures = []
identity_green = unreal.EditorAssetLibrary.load_asset(
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v085")
identity_screen = unreal.EditorAssetLibrary.load_asset(
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_HMIScreenOnline_v085")
if identity_green is None:
    failures.append("shared Cairnwell green identity material missing")
if identity_screen is None:
    failures.append("shared HMI screen identity material missing")

label_material_path = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103/Materials/M_CA_MW_PR010_StackLabel_v103"
label_material = unreal.EditorAssetLibrary.load_asset(label_material_path)
if label_material is None:
    label_material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_CA_MW_PR010_StackLabel_v103",
        "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103/Materials",
        unreal.Material, unreal.MaterialFactoryNew())
    if label_material is not None:
        editing = unreal.MaterialEditingLibrary
        base = editing.create_material_expression(label_material, unreal.MaterialExpressionConstant3Vector, -400, -100)
        base.set_editor_property("constant", unreal.LinearColor(0.018, 0.11, 0.08, 1.0))
        roughness = editing.create_material_expression(label_material, unreal.MaterialExpressionConstant, -400, 50)
        roughness.set_editor_property("r", 0.58)
        metallic = editing.create_material_expression(label_material, unreal.MaterialExpressionConstant, -400, 150)
        metallic.set_editor_property("r", 0.04)
        emissive = editing.create_material_expression(label_material, unreal.MaterialExpressionConstant3Vector, -400, 260)
        emissive.set_editor_property("constant", unreal.LinearColor(0.03, 0.42, 0.28, 1.0))
        editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        editing.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
        editing.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
        editing.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        editing.recompile_material(label_material)
        unreal.EditorAssetLibrary.save_asset(label_material_path, only_if_is_dirty=False)
if label_material is None:
    failures.append("could not create calibrated v103 stack-label material")
for actor in plates:
    value = actor.get_actor_label().split("StackIDPlate_", 1)[-1].replace("__", "  ").replace("_", " ")
    stack = stack_for(value)
    location = stack.get_actor_location() if stack else actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x, location.y + 112.0, 87.0), False, False)
    actor.set_actor_rotation(unreal.Rotator(yaw=180), False)
    if label_material is not None:
        actor.static_mesh_component.set_material(0, label_material)
        actor.static_mesh_component.set_material(1, label_material)
for actor in texts:
    value = str(actor.text_render.get_editor_property("text"))
    stack = stack_for(value)
    location = stack.get_actor_location() if stack else actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x, location.y + 118.0, 103.0), False, False)
    actor.set_actor_rotation(unreal.Rotator(yaw=90), False)
    actor.text_render.set_world_size(7.0)
    actor.text_render.set_text_render_color(unreal.Color(8, 25, 20, 255))
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_visibility(False, True)
    actor.text_render.set_editor_property("hidden_in_game", True)
    actor.set_actor_hidden_in_game(True)

    reverse = reverse_by_value.get(value)
    if reverse is None:
        reverse = actors_api.spawn_actor_from_class(
            unreal.TextRenderActor, unreal.Vector(location.x, location.y + 118.2, 103.0), unreal.Rotator(yaw=-90))
        reverse.set_actor_label("LB_PR010_V103_TEXT_StackID_Reverse_" + value.replace(" ", "_"))
        reverse.tags = [unreal.Name(tag) for tag in (
            "LB.Station.PR010", "LB.Asset.Candidate.v103", "LB.Asset.CandidateNotPromoted",
            "LB.Identity.Traceability", "LB.PR010.StackPositionID.Reverse.v103")]
        reverse.text_render.set_text(value)
        reverse_by_value[value] = reverse
    reverse.text_render.set_relative_scale3d(unreal.Vector(1.0, -1.0, 1.0))
    reverse.text_render.set_text_render_color(unreal.Color(235, 240, 235, 255))
    reverse.text_render.set_visibility(True, True)
    reverse.text_render.set_editor_property("hidden_in_game", False)
    reverse.set_actor_hidden_in_game(False)

representative = next((actor for actor in texts if str(actor.text_render.get_editor_property("text")).startswith("A1")), None)
camera = next((actor for actor in actors if actor.get_actor_label() == "LB_PR010_V103_CAM_StackID"), None)
if representative is None:
    failures.append("representative A1 stack ID text missing")
else:
    target = representative.get_actor_location()
    # Approach from the same north/east side as the fixed overview camera; the
    # plate is mounted on that genuinely visible stack face.
    location = unreal.Vector(target.x + 250.0, target.y + 350.0, 230.0)
    rotation = unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(target.x, target.y, 24.0))
    if camera is None:
        camera = actors_api.spawn_actor_from_class(unreal.CameraActor, location, rotation)
        camera.set_actor_label("LB_PR010_V103_CAM_StackID")
    else:
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(rotation, False)
    camera.tags = [unreal.Name(value) for value in (
        "LB.Station.PR010", "LB.Asset.Candidate.v103", "LB.Asset.CandidateNotPromoted",
        "LB.Camera.Fixed.PR010.v103", "LB.Camera.Evidence.StackID")]
    camera.camera_component.set_editor_property("field_of_view", 42.0)
if len(texts) != 9:
    failures.append(f"expected nine v103 stack ID texts, found {len(texts)}")
if len(plates) != 9:
    failures.append(f"expected nine v103 stack ID plates, found {len(plates)}")
if len(reverse_by_value) != 9:
    failures.append(f"expected nine reverse-facing v103 stack ID texts, found {len(reverse_by_value)}")
if not levels.save_current_level():
    failures.append("could not save corrected v103 map")
report = {
    "$schema": "cairnwell/audit/pr010-stack-id-legibility-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V103_STACK_ID_TEXT_CCTV_SCALE_AND_FIXED_CAMERA__FRESH_EVIDENCE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V103_STACK_ID_CORRECTION__NOT_PROMOTED",
    "map": MAP, "stack_id_text_count": len(texts), "stack_id_plate_count": len(plates),
    "reverse_stack_id_text_count": len(reverse_by_value),
    "plate_base_z_cm": 87.0, "text_centre_z_cm": 103.0, "world_size_cm": 7.0,
    "camera": camera.get_actor_label() if camera else None,
    "failures": failures, "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
