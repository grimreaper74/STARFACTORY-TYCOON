"""Build a disposable visual QA map for the texture-preserving PR005 HMI candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
MESH_PATH = (
    "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/HMI_v001/"
    "SM_CA_Factory_OperatorHMI_MeshyMaster_v632/StaticMeshes/"
    "SM_CA_MW_PR005_dHMI_Meshy_v001"
)
MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_DetailedHMI_v001"
OUTPUT = PROJECT / "Saved/ValidationScreenshots/PR005/HMI/Candidate_v001/pr005_detailed_hmi_texture_v001.png"
AUDIT = PROJECT / "Saved/Audits/PR005/HMI_v001/pr005_detailed_hmi_render_validation_v001.json"


def add_light(actors, label, location, target, intensity, width, height):
    light = actors.spawn_actor_from_class(unreal.RectLight, location, unreal.Rotator())
    light.set_actor_label(label)
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    light.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": intensity, "attenuation_radius": 900.0,
        "source_width": width, "source_height": height,
    })
    return light


def main() -> None:
    mesh = unreal.load_asset(MESH_PATH)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing PR005 detailed HMI candidate: {MESH_PATH}")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    library = unreal.EditorAssetLibrary
    if library.does_asset_exist(MAP):
        levels.load_level(MAP)
        for actor in actors.get_all_level_actors():
            actors.destroy_actor(actor)
    elif not levels.new_level(MAP):
        raise RuntimeError(f"Could not create visual QA map {MAP}")

    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -6), unreal.Rotator())
    floor.set_actor_label("PR005_HMI_QA_Floor")
    floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    floor.set_actor_scale3d(unreal.Vector(4.0, 4.0, 0.06))
    concrete = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete")
    if concrete:
        floor.static_mesh_component.set_material(0, concrete)

    hmi = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator(0, 180, 0))
    hmi.set_actor_label("PR005_DetailedHMI_Meshy_v001_TexturePreservation")
    hmi.static_mesh_component.set_static_mesh(mesh)
    hmi.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    add_light(actors, "PR005_HMI_QA_Key", unreal.Vector(-150, 230, 210), unreal.Vector(0, 0, 70), 900.0, 130.0, 130.0)
    add_light(actors, "PR005_HMI_QA_Fill", unreal.Vector(170, 90, 145), unreal.Vector(0, 0, 65), 450.0, 100.0, 100.0)
    add_light(actors, "PR005_HMI_QA_Rim", unreal.Vector(-120, -180, 195), unreal.Vector(0, 0, 85), 650.0, 90.0, 90.0)

    exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    exposure.set_actor_label("PR005_HMI_QA_FixedExposure")
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.0,
    })
    exposure.set_editor_property("settings", settings)

    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(150, 250, 135), unreal.Rotator())
    camera.set_actor_label("PR005_HMI_QA_Camera")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 66)), False)
    camera.camera_component.set_editor_property("field_of_view", 36.0)
    if not levels.save_current_level():
        raise RuntimeError("Could not save HMI QA map")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "viewmode lit")
    unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "r.ForceDebugViewModes 0")
    unreal.EditorLevelLibrary.editor_set_game_view(True)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(OUTPUT), camera=camera, mask_enabled=False, capture_hdr=False,
        comparison_tolerance=unreal.ComparisonTolerance.LOW,
        comparison_notes="PR005 detailed Meshy HMI original PBR texture validation",
        delay=0.5, force_game_view=True,
    )
    if not task.is_valid_task():
        raise RuntimeError("Unreal did not start HMI screenshot")
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "status": "CANDIDATE_ONLY__RENDER_REQUESTED__NO_RUNTIME_BINDING",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "qa_map": MAP,
        "mesh": mesh.get_path_name(),
        "screenshot": str(OUTPUT),
        "collision": "NO_COLLISION",
        "navigation": "OFF",
        "overlaps": "OFF",
        "texture_policy": "ORIGINAL_PBR_TEXTURE_ATLAS_RETAINED",
        "v913_change": "NONE",
        "runtime_binding": "NONE",
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR005_DETAILED_HMI_QA_RENDER_REQUESTED output={OUTPUT}")


main()
