"""Build a direct-v107 cumulative merge of retained local PR005-PR008 work.

The four retained station candidates are read-only donor specifications.  Only
their station-local added actors and exact inherited overrides are replayed on
a fresh v107 child; no donor map is used as a parent or modified.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"
MAP = "/Game/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v211"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_cumulative_release_build_v211.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

DONORS = [
    ("PR005", "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v205", "LB_PR005_V205_"),
    ("PR006", "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208", "LB_PR006_V208_"),
    ("PR007", "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209", "LB_PR007_V209_"),
    ("PR008", "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210", "LB_PR008_V210_"),
]
PR005_OLD = {
    "LB_PR005_V053_ReturnStillage_Base", "LB_PR005_V053_ReturnStillage_Open",
    "LB_PR005_V053_ServicePallet", "LB_PR005_V053_ServiceCrate_01",
    "LB_PR005_V053_ServiceCrate_02", "LB_PR005_V053_ServiceCrate_03",
}
INFILL = "LB_PR005_V197_RuntimeCageInfill_Static_v005"
INHERITED_LIGHTS = {
    "PR006": ("LB_PR006_V054_OperatorTaskLight", "LB_PR006_V054_DriveTaskLight"),
    "PR007": ("LB_PR007_V055_OperatorTask", "LB_PR007_V055_ServiceTask"),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def prop(component, name, default=None):
    try:
        return component.get_editor_property(name)
    except Exception:
        return default


def serialize_actor(actor):
    record = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "tags": [str(value) for value in actor.tags],
    }
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        mesh = prop(component, "static_mesh")
        record["static_mesh"] = mesh.get_path_name() if mesh else None
        count = len(mesh.get_editor_property("static_materials")) if mesh else 0
        record["materials"] = [
            component.get_material(index).get_path_name() if component.get_material(index) else None
            for index in range(count)
        ]
        record["collision_enabled"] = prop(component, "collision_enabled")
        record["collision_profile_name"] = prop(component, "collision_profile_name")
        record["affects_navigation"] = bool(prop(component, "can_ever_affect_navigation", False))
        record["cast_shadow"] = bool(prop(component, "cast_shadow", True))
        record["mobility"] = prop(component, "mobility")
    elif isinstance(actor, unreal.PointLight):
        component = actor.point_light_component
        record["light"] = {name: prop(component, name) for name in (
            "intensity", "attenuation_radius", "cast_shadows", "light_color",
            "source_radius", "soft_source_radius", "source_length")}
    elif isinstance(actor, unreal.RectLight):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        record["light"] = {name: prop(component, name) for name in (
            "intensity", "attenuation_radius", "cast_shadows", "light_color",
            "source_width", "source_height", "barn_door_angle", "barn_door_length")}
    elif isinstance(actor, unreal.CameraActor):
        component = actor.camera_component
        record["camera"] = {name: prop(component, name) for name in (
            "field_of_view", "aspect_ratio", "constrain_aspect_ratio")}
    else:
        raise RuntimeError(f"unsupported donor actor class {record['class']} for {record['label']}")
    return record


def serialize_spot(actor):
    if not isinstance(actor, unreal.SpotLight):
        raise RuntimeError(f"expected SpotLight donor {actor.get_actor_label()}")
    component = actor.spot_light_component
    return {
        "tags": [str(value) for value in actor.tags],
        "properties": {name: prop(component, name) for name in (
            "intensity", "attenuation_radius", "inner_cone_angle", "outer_cone_angle",
            "source_radius", "soft_source_radius", "cast_shadows", "light_color")},
    }


base_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap"
protected_paths = {"v107": base_file}
for station, donor_map, _ in DONORS:
    protected_paths[station] = ROOT / ("Content" + donor_map.removeprefix("/Game").replace("/", "\\") + ".umap")
protected_before = {key: sha256(path) for key, path in protected_paths.items()}

donor_records = {}
infill_materials = None
spot_overrides = {}
for station, donor_map, prefix in DONORS:
    if not levels.load_level(donor_map):
        raise RuntimeError(f"could not load read-only donor {donor_map}")
    actors = list(actors_api.get_all_level_actors())
    rows = [serialize_actor(actor) for actor in actors if actor.get_actor_label().startswith(prefix)]
    donor_records[station] = rows
    if station == "PR005":
        infill_rows = [actor for actor in actors if actor.get_actor_label() == INFILL]
        if len(infill_rows) != 1:
            raise RuntimeError(f"expected one donor PR005 infill, got {len(infill_rows)}")
        component = infill_rows[0].static_mesh_component
        mesh = component.get_editor_property("static_mesh")
        infill_materials = [
            component.get_material(index).get_path_name() if component.get_material(index) else None
            for index in range(len(mesh.get_editor_property("static_materials")))
        ]
    for label in INHERITED_LIGHTS.get(station, ()):
        matches = [actor for actor in actors if actor.get_actor_label() == label]
        if len(matches) != 1:
            raise RuntimeError(f"expected one donor inherited light {label}, got {len(matches)}")
        spot_overrides[label] = serialize_spot(matches[0])

expected_counts = {"PR005": 3, "PR006": 15, "PR007": 15, "PR008": 9}
actual_counts = {station: len(rows) for station, rows in donor_records.items()}
if actual_counts != expected_counts:
    raise RuntimeError(f"donor actor count mismatch {actual_counts}")
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create direct-v107 cumulative candidate {MAP}")

target_actors = list(actors_api.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in target_actors}
removed_pr005 = []
for label in sorted(PR005_OLD):
    actor = by_label.get(label)
    if actor is None or not actors_api.destroy_actor(actor):
        raise RuntimeError(f"could not remove inherited PR005 logistics actor {label}")
    removed_pr005.append(label)

infill_rows = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == INFILL]
if len(infill_rows) != 1 or infill_materials is None:
    raise RuntimeError("target PR005 infill/material donor mismatch")
infill_component = infill_rows[0].static_mesh_component
for index, material_path in enumerate(infill_materials):
    if material_path:
        material = library.load_asset(material_path)
        if material is None:
            raise RuntimeError(f"missing donor infill material {material_path}")
        infill_component.set_material(index, material)
infill_rows[0].tags = list(infill_rows[0].tags) + [unreal.Name("LB.Merge.Cumulative.v211")]

old_anchor_actors = [actor for actor in actors_api.get_all_level_actors()
                     if actor.get_actor_label().startswith("LB_PR008_V082_Base")
                     and (actor.get_actor_label().endswith("_Plate") or actor.get_actor_label().endswith("_Stud"))]
if len(old_anchor_actors) != 48:
    raise RuntimeError(f"expected 48 generic PR008 anchors in fresh v107 child, got {len(old_anchor_actors)}")
removed_pr008 = sorted(actor.get_actor_label() for actor in old_anchor_actors)
for actor in old_anchor_actors:
    if not actors_api.destroy_actor(actor):
        raise RuntimeError(f"could not remove {actor.get_actor_label()}")

spawn_classes = {
    "StaticMeshActor": unreal.StaticMeshActor,
    "PointLight": unreal.PointLight,
    "RectLight": unreal.RectLight,
    "CameraActor": unreal.CameraActor,
}
spawned = []
for station in ("PR005", "PR006", "PR007", "PR008"):
    for record in donor_records[station]:
        cls = spawn_classes[record["class"]]
        rotation = unreal.Rotator()
        rotation.set_editor_properties({
            "pitch": record["rotation"][0],
            "yaw": record["rotation"][1],
            "roll": record["rotation"][2],
        })
        actor = actors_api.spawn_actor_from_class(cls, unreal.Vector(*record["location"]), rotation)
        if actor is None:
            raise RuntimeError(f"could not spawn donor {record['label']}")
        actor.set_actor_label(record["label"])
        actor.set_actor_scale3d(unreal.Vector(*record["scale"]))
        actor.tags = [unreal.Name(value) for value in record["tags"]] + [unreal.Name("LB.Merge.Cumulative.v211")]
        if record["class"] == "StaticMeshActor":
            component = actor.static_mesh_component
            mesh = library.load_asset(record["static_mesh"])
            if not isinstance(mesh, unreal.StaticMesh):
                raise RuntimeError(f"missing donor mesh {record['static_mesh']}")
            component.set_static_mesh(mesh)
            for index, material_path in enumerate(record["materials"]):
                if material_path:
                    material = library.load_asset(material_path)
                    if material is None:
                        raise RuntimeError(f"missing donor material {material_path}")
                    component.set_material(index, material)
            component.set_collision_enabled(record["collision_enabled"])
            component.set_collision_profile_name(record["collision_profile_name"])
            component.set_editor_property("can_ever_affect_navigation", record["affects_navigation"])
            component.set_editor_property("cast_shadow", record["cast_shadow"])
            component.set_mobility(record["mobility"])
        elif record["class"] == "PointLight":
            props = {key: value for key, value in record["light"].items() if value is not None}
            actor.point_light_component.set_editor_properties(props)
        elif record["class"] == "RectLight":
            props = {key: value for key, value in record["light"].items() if value is not None}
            actor.get_component_by_class(unreal.RectLightComponent).set_editor_properties(props)
        elif record["class"] == "CameraActor":
            props = {key: value for key, value in record["camera"].items() if value is not None}
            actor.camera_component.set_editor_properties(props)
        spawned.append(record["label"])

target_by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
for label, donor in spot_overrides.items():
    actor = target_by_label.get(label)
    if not isinstance(actor, unreal.SpotLight):
        raise RuntimeError(f"missing target inherited light {label}")
    actor.spot_light_component.set_editor_properties({
        key: value for key, value in donor["properties"].items() if value is not None})
    actor.tags = [unreal.Name(value) for value in donor["tags"]] + [unreal.Name("LB.Merge.Cumulative.v211")]

failures = []
all_labels = [actor.get_actor_label() for actor in actors_api.get_all_level_actors()]
for station, rows in donor_records.items():
    missing = sorted(record["label"] for record in rows if record["label"] not in all_labels)
    if missing:
        failures.append(f"missing {station} donor labels: {missing}")
if any(label in all_labels for label in PR005_OLD):
    failures.append("superseded PR005 v053 logistics remain")
remaining_pr008 = [label for label in all_labels if label.startswith("LB_PR008_V082_Base")
                   and (label.endswith("_Plate") or label.endswith("_Stud"))]
if remaining_pr008:
    failures.append(f"generic PR008 anchors remain: {len(remaining_pr008)}")
if not levels.save_current_level():
    failures.append("could not save v211")

protected_after = {key: sha256(path) for key, path in protected_paths.items()}
for key in protected_before:
    if protected_before[key] != protected_after[key]:
        failures.append(f"protected source changed: {key}")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v211.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-cumulative-release-build-v211/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DIRECT_V107_CUMULATIVE_LOCAL_MERGE__TECHNICAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "map_sha256": sha256(map_file) if map_file.exists() else None,
    "protected_sha256_before": protected_before,
    "protected_sha256_after": protected_after,
    "donor_actor_counts": actual_counts,
    "spawned_actor_count": len(spawned),
    "removed_pr005_v053_actor_count": len(removed_pr005),
    "removed_pr008_v082_anchor_actor_count": len(removed_pr008),
    "inherited_spot_overrides": sorted(spot_overrides),
    "native_runtime_authority_modified": False,
    "promotion_authorized": False,
    "failures": failures,
  }
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_CUMULATIVE_RELEASE_V211_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
