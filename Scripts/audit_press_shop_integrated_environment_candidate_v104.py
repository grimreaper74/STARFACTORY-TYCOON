"""Read-only static gate for the isolated Press Shop environment v104 candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v104"
OUT = ROOT / "Saved/Audits/PressShopIntegration/integrated_environment_static_gate_v104.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")

actors = actors_api.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
failures = []

expected_cameras = [
    "LB_ENV_V104_CAM_WholeShop",
    "LB_ENV_V104_CAM_FrontEnd",
    "LB_ENV_V104_CAM_CraneCoil",
    "LB_ENV_V104_CAM_ConnectedLine",
]
missing_cameras = [label for label in expected_cameras if label not in by_label]
if missing_cameras:
    failures.append(f"missing fixed cameras: {missing_cameras}")

expected_floor_roles = {
    "LB_INT_FRONT_Floor_PR001": "M_CA_MW_ReceivingConcrete_v104",
    "LB_INT_FRONT_Floor_PR002": "M_CA_MW_InspectionConcrete_v104",
    "LB_INT_FRONT_Floor_HOLD": "M_CA_MW_HoldConcrete_v104",
    "LB_INT_FRONT_Floor_PR003": "M_CA_MW_CoilStoreConcrete_v104",
    "LB_INT_FRONT_PedestrianRoute": "M_CA_MW_ProtectedWalkway_v104",
}
floor_bindings = {}
for label, material_token in expected_floor_roles.items():
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"missing floor actor: {label}")
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    paths = [] if component is None else [
        component.get_material(index).get_path_name() if component.get_material(index) else None
        for index in range(component.get_num_materials())
    ]
    floor_bindings[label] = paths
    if not any(path and material_token in path for path in paths):
        failures.append(f"incorrect v104 material on {label}: {paths}")

directionals = []
skylights = []
for actor in actors:
    if isinstance(actor, unreal.DirectionalLight):
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
        row = {
            "label": actor.get_actor_label(),
            "affects_world": bool(component.get_editor_property("affects_world")),
            "intensity": float(component.get_editor_property("intensity")),
            "forward_shading_priority": int(component.get_editor_property("forward_shading_priority")),
        }
        directionals.append(row)
    elif isinstance(actor, unreal.SkyLight):
        component = actor.get_component_by_class(unreal.SkyLightComponent)
        skylights.append({
            "label": actor.get_actor_label(),
            "real_time_capture": bool(component.get_editor_property("real_time_capture")),
            "affects_world": bool(component.get_editor_property("affects_world")),
        })

active_directionals = [row for row in directionals if row["affects_world"] and row["intensity"] > 0.0]
if len(active_directionals) != 1:
    failures.append(f"expected one active directional light, found {len(active_directionals)}")
elif active_directionals[0]["forward_shading_priority"] != 1:
    failures.append("active directional light does not own forward shading priority 1")
if any(row["real_time_capture"] for row in skylights):
    failures.append("a skylight still has real-time capture enabled")

disabled_prefixes = (
    "LB_MOTH_V004_EmergencyPool_",
    "LB_PR004_V028_",
    "LB_PR004_V031_",
    "LB_PR004_V034_",
    "LB_PR004_V037_",
    "LB_PR004_V040_",
    "LB_PR008_V058_",
    "LB_PR008_V062_",
)
superseded_active = []
for actor in actors:
    label = actor.get_actor_label()
    if not label.startswith(disabled_prefixes):
        continue
    component = actor.get_component_by_class(unreal.LightComponent)
    if component and bool(component.get_editor_property("affects_world")):
        superseded_active.append(label)
if superseded_active:
    failures.append(f"superseded lights remain active: {superseded_active}")

required_authority_tokens = ("LB.Asset.Accepted.PR009.v096", "LB.Asset.Accepted.PR010.v103")
tag_text = "\n".join(str(tag) for actor in actors for tag in actor.tags)
missing_authority_tokens = [token for token in required_authority_tokens if token not in tag_text]
if missing_authority_tokens:
    failures.append(f"accepted authority tags missing: {missing_authority_tokens}")

payload = {
    "$schema": "cairnwell/audit/press-shop-integrated-environment-static-gate-v104/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "map": MAP,
    "actor_count": len(actors),
    "fixed_cameras": expected_cameras,
    "missing_cameras": missing_cameras,
    "floor_bindings": floor_bindings,
    "directional_lights": directionals,
    "active_directional_lights": active_directionals,
    "sky_lights": skylights,
    "superseded_active_lights": superseded_active,
    "missing_authority_tokens": missing_authority_tokens,
    "failures": failures,
    "accepted_v103_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
