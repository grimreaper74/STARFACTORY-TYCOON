"""Replace the v024 cosmetic PR-004 coil with the native authoritative station presentation."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
STATIC_COIL_LABEL = "LB_INT_PR004_V024_WrappedCoilOnPreparationStand"
STATION_LABEL = "LB_INT_PR004_V024_InteractiveUnpackageStation"
WRAPPED_MESH_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/SM_LB_MasterCoil_Candidate_v002"
BARE_MESH_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021"
BARE_MATERIAL_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v023/M_LB_BareCoil_WoundSteel_v023"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_interactive_coil_binding_v024.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
if any(actor.get_actor_label() == STATION_LABEL for actor in actors.get_all_level_actors()):
    raise RuntimeError(f"Refusing duplicate station binding: {STATION_LABEL}")
source = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == STATIC_COIL_LABEL), None)
if source is None:
    raise RuntimeError(f"Missing cosmetic source coil: {STATIC_COIL_LABEL}")

wrapped_mesh = lib.load_asset(WRAPPED_MESH_PATH)
bare_mesh = lib.load_asset(BARE_MESH_PATH)
bare_material = lib.load_asset(BARE_MATERIAL_PATH)
if wrapped_mesh is None or bare_mesh is None or bare_material is None:
    raise RuntimeError("One or more PR-004 interactive presentation assets are missing")

transform = source.get_actor_transform()
station = actors.spawn_actor_from_class(unreal.LBPR004Station, source.get_actor_location(), source.get_actor_rotation())
if station is None:
    raise RuntimeError("Could not spawn native LBPR004Station")
station.set_actor_scale3d(transform.scale3d)
station.set_actor_label(STATION_LABEL)
station.tags = [
    unreal.Name("LB.Asset.Candidate.v024"),
    unreal.Name("LB.PR004.Interaction.Unpackage"),
    unreal.Name("LB.PR004.Authority.Native"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

components = {component.get_name(): component for component in station.get_components_by_class(unreal.StaticMeshComponent)}
wrapped = components.get("PR004_WrappedCoilVisual")
bare = components.get("PR004_BareCoilVisual")
if wrapped is None or bare is None:
    raise RuntimeError(f"Native presentation components missing: {sorted(components.keys())}")

wrapped.set_static_mesh(wrapped_mesh)
wrapped.set_editor_property("override_materials", [])
wrapped.set_visibility(True, True)
wrapped.set_hidden_in_game(False, True)
wrapped.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)

wrapped_box = wrapped_mesh.get_bounding_box()
bare_box = bare_mesh.get_bounding_box()
bare_z = float(wrapped_box.min.z - bare_box.min.z)
bare.set_static_mesh(bare_mesh)
bare.set_material(0, bare_material)
bare.set_relative_location(unreal.Vector(0.0, 0.0, bare_z), False, False)
bare.set_visibility(False, True)
bare.set_hidden_in_game(True, True)
bare.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

actors.destroy_actor(source)
if any(actor.get_actor_label() == STATIC_COIL_LABEL for actor in actors.get_all_level_actors()):
    raise RuntimeError("Cosmetic source coil remains after native station binding")
if not levels.save_current_level():
    raise RuntimeError("Could not save interactive v024 map")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-interactive-coil-binding-v024/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_INTERACTIVE_PRESENTATION_BOUND__RUNTIME_AND_VISUAL_GATES_OPEN__NOT_PROMOTED",
    "map": MAP,
    "removed_cosmetic_actor": STATIC_COIL_LABEL,
    "native_station_actor": station.get_actor_label(),
    "native_class": station.get_class().get_path_name(),
    "wrapped_component": {
        "name": wrapped.get_name(),
        "mesh": wrapped_mesh.get_path_name(),
        "editor_visible": True,
        "collision": "QUERY_ONLY",
    },
    "bare_component": {
        "name": bare.get_name(),
        "mesh": bare_mesh.get_path_name(),
        "material": bare_material.get_path_name(),
        "relative_z_cm": bare_z,
        "editor_visible": False,
        "collision": "NO_COLLISION_UNTIL_UNPACKAGED",
    },
    "interaction_authority": "ALBPR004Station.UnpackageCoil",
    "save_authority": "FLBPR004SaveState via ALBPR004Station.GetStableSaveState/RestoreSaveState",
    "accepted_v006_preserved": True,
    "promotion_authorized": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_INTERACTIVE_COIL_V024_BIND_PASS station={STATION_LABEL}")
unreal.SystemLibrary.quit_editor()
