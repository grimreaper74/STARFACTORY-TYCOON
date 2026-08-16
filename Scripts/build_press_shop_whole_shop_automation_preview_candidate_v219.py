"""Install retained Press Trains A-D into corrected cumulative v218.

This is an EST-P owner-inspection preview, not production placement authority.
All retained source maps are read-only and preserved byte-for-byte.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v218"
MAP = "/Game/LineBoss/Maps/LB_PressShop_WholeShopAutomationPreviewCandidate_v219"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_whole_shop_automation_preview_build_v219.json"
DONORS = {
    "A": "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027",
    "B": "/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001",
    "C": "/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001",
    "D": "/Game/LineBoss/Maps/LB_PressTrainDIsolatedVariantCandidate_v001",
}

# EST-P centres from press_shop_master_plan_anchors_v001.json.  The explicit
# authority gap remains: these are preview transforms, never production datums.
INSTALL = {
    "A": {"origin": (1600.0, -4300.0, 0.0), "yaw": -90.0,
          "display": "TRAIN A", "family": "LARGE OUTER PANELS", "accent": (0.231, 0.510, 0.769, 1.0)},
    "B": {"origin": (1600.0, -2600.0, 0.0), "yaw": -90.0,
          "display": "TRAIN B", "family": "FLOORS / UNDERBODY", "accent": (0.302, 0.545, 0.290, 1.0)},
    "C": {"origin": (1600.0, -900.0, 0.0), "yaw": -90.0,
          "display": "TRAIN C", "family": "CLOSURES", "accent": (0.784, 0.471, 0.176, 1.0)},
    "D": {"origin": (1600.0, 800.0, 0.0), "yaw": -90.0,
          "display": "TRAIN D", "family": "REINFORCEMENTS / SMALLER PANELS", "accent": (0.459, 0.341, 0.561, 1.0)},
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def transform_record(actor):
    return {
        "location": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
    }


def make_transform(record):
    return unreal.Transform(
        location=unreal.Vector(*record["location"]),
        rotation=unreal.Rotator(*record["rotation"]),
        scale=unreal.Vector(*record["scale"]),
    )


def installed_transform(train, record):
    spec = INSTALL[train]
    install = unreal.Transform(
        location=unreal.Vector(*spec["origin"]),
        rotation=unreal.Rotator(0.0, spec["yaw"], 0.0),
        scale=unreal.Vector(1.0, 1.0, 1.0),
    )
    return unreal.MathLibrary.compose_transforms(make_transform(record), install)


def protected_file(map_path):
    return ROOT / ("Content" + map_path.removeprefix("/Game").replace("/", "\\") + ".umap")


protected = {"v190": protected_file("/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190"),
             "v218": protected_file(BASE)}
for train, path in DONORS.items():
    protected[f"train_{train}"] = protected_file(path)
protected_before = {key: sha256(path) for key, path in protected.items()}

donor_records = {}
for train, donor_map in DONORS.items():
    if not levels.load_level(donor_map):
        raise RuntimeError(f"could not load retained donor {donor_map}")
    static_records = []
    text_records = []
    station_count = 0
    for actor in actors_api.get_all_level_actors():
        tags = [str(tag) for tag in actor.tags]
        label = actor.get_actor_label()
        if isinstance(actor, unreal.StaticMeshActor):
            # Exactly one static actor in each donor is the isolated validation
            # floor.  Machinery and its physical proxies carry this flow tag.
            if "LB.PressTrain.ProcessDirection.PositiveY" not in tags:
                continue
            component = actor.static_mesh_component
            mesh = prop(component, "static_mesh")
            if not isinstance(mesh, unreal.StaticMesh):
                raise RuntimeError(f"missing source mesh on {train}:{label}")
            static_records.append({
                "label": label,
                "transform": transform_record(actor),
                "tags": tags,
                "parent": actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else None,
                "mesh": mesh.get_path_name(),
                "materials": [
                    component.get_material(index).get_path_name() if component.get_material(index) else None
                    for index in range(component.get_num_materials())
                ],
                "collision_enabled": component.get_collision_enabled(),
                "collision_profile": component.get_collision_profile_name(),
                "affects_navigation": bool(prop(component, "can_ever_affect_navigation", False)),
                "cast_shadow": bool(prop(component, "cast_shadow", True)),
                "mobility": prop(component, "mobility"),
            })
        elif actor.get_class().get_name() == "LBPressTrainAStation":
            station_count += 1
        elif isinstance(actor, unreal.TextRenderActor) and any(
                tag in tags for tag in ("LB.HMI.PressTrain.LiveState", "LB.HMI.PressTrainA.LiveState",
                                        f"LB.HMI.PressTrain{train}.LiveState")):
            component = actor.text_render
            text_records.append({
                "label": label,
                "transform": transform_record(actor),
                "tags": tags,
                "parent": actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else None,
                "text": str(prop(component, "text", "")),
                "world_size": float(prop(component, "world_size", 24.0)),
                "color": prop(component, "text_render_color", unreal.Color(220, 235, 225, 255)),
                "horizontal_alignment": prop(component, "horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER),
                "vertical_alignment": prop(component, "vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER),
            })
    if len(static_records) != 336 or len(text_records) != 1 or station_count != 1:
        raise RuntimeError(
            f"donor contract mismatch {train}: static={len(static_records)} text={len(text_records)} station={station_count}")
    donor_records[train] = {"static": static_records, "text": text_records}

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create {MAP} from {BASE}")

spawned_by_train = {}
hierarchy_edges = []
for train in "ABCD":
    scope = f"LB.PressTrain.Installed.TRAIN_{train}"
    spawned = {}
    for record in donor_records[train]["static"]:
        target = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
        if target is None:
            raise RuntimeError(f"could not spawn {train}:{record['label']}")
        target.set_actor_label(f"LB_INST_PT{train}_{record['label']}")
        component = target.static_mesh_component
        mesh = library.load_asset(record["mesh"])
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"missing retained mesh {record['mesh']}")
        component.set_static_mesh(mesh)
        for index, material_path in enumerate(record["materials"]):
            if material_path:
                material = library.load_asset(material_path)
                if material is None:
                    raise RuntimeError(f"missing retained material {material_path}")
                component.set_material(index, material)
        component.set_collision_enabled(record["collision_enabled"])
        component.set_collision_profile_name(record["collision_profile"])
        component.set_editor_property("can_ever_affect_navigation", record["affects_navigation"])
        component.set_editor_property("cast_shadow", record["cast_shadow"])
        component.set_mobility(record["mobility"])
        target.set_actor_transform(installed_transform(train, record["transform"]), False, True)
        target.tags = [unreal.Name(value) for value in record["tags"]] + [unreal.Name(value) for value in (
            scope, "LB.LayoutAuthority.EST-P.ReferenceOnly", "LB.Asset.Candidate.v219",
            "LB.Asset.CandidateNotPromoted", "LB.Integration.WholeShopAutomationPreview.v219")]
        spawned[record["label"]] = target
    for record in donor_records[train]["text"]:
        target = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(), unreal.Rotator())
        if target is None:
            raise RuntimeError(f"could not spawn HMI text {train}")
        target.set_actor_label(f"LB_INST_PT{train}_{record['label']}")
        target.set_actor_transform(installed_transform(train, record["transform"]), False, True)
        target.tags = [unreal.Name(value) for value in record["tags"]] + [unreal.Name(value) for value in (
            scope, "LB.LayoutAuthority.EST-P.ReferenceOnly", "LB.Asset.Candidate.v219",
            "LB.Asset.CandidateNotPromoted", "LB.Integration.WholeShopAutomationPreview.v219")]
        target.text_render.set_text(record["text"])
        target.text_render.set_world_size(record["world_size"])
        target.text_render.set_text_render_color(record["color"])
        target.text_render.set_horizontal_alignment(record["horizontal_alignment"])
        target.text_render.set_vertical_alignment(record["vertical_alignment"])
        target.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        target.text_render.set_editor_property("can_ever_affect_navigation", False)
        spawned[record["label"]] = target

    for record in donor_records[train]["static"] + donor_records[train]["text"]:
        if not record["parent"]:
            continue
        child = spawned.get(record["label"])
        parent = spawned.get(record["parent"])
        if child is None or parent is None:
            raise RuntimeError(f"missing hierarchy endpoint {train}:{record['label']}->{record['parent']}")
        if not child.attach_to_actor(parent, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
                                     unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError(f"could not restore hierarchy {train}:{record['label']}->{record['parent']}")
        hierarchy_edges.append((train, record["label"], record["parent"]))

    station = actors_api.spawn_actor_from_class(unreal.LBPressTrainAStation, unreal.Vector(), unreal.Rotator())
    if station is None:
        raise RuntimeError(f"could not spawn native Train {train} authority")
    station.set_actor_label(f"LB_INST_PT{train}_NativeAuthority_v219")
    station.set_actor_transform(installed_transform(train, {
        "location": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]}), False, True)
    spec = INSTALL[train]
    if not station.configure_train_variant(unreal.Name(f"TRAIN_{train}"), spec["display"], spec["family"],
                                           unreal.LinearColor(*spec["accent"])):
        raise RuntimeError(f"native Train {train} variant configuration rejected")
    station.tags = [unreal.Name(value) for value in (
        scope, f"LB.Station.PressTrain{train}", "LB.Authority.Native",
        "LB.LayoutAuthority.EST-P.ReferenceOnly", "LB.Asset.Candidate.v219",
        "LB.Asset.CandidateNotPromoted", "LB.Integration.WholeShopAutomationPreview.v219")]
    spawned_by_train[train] = len(spawned) + 1


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        raise RuntimeError(f"could not spawn camera {label}")
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.WholeShopAutomation.v219",
        "LB.LayoutAuthority.EST-P.ReferenceOnly", "LB.Asset.Candidate.v219",
        "LB.Asset.CandidateNotPromoted")]
    return camera.get_actor_label()


cameras = [
    add_camera("LB_WHOLE_V219_CAM_FourTrainsManagement", (-350.0, 4500.0, 1450.0), (3850.0, -1750.0, 380.0), 48.0),
    add_camera("LB_WHOLE_V219_CAM_FourTrainsSouth", (650.0, -5600.0, 1000.0), (3850.0, -1750.0, 420.0), 50.0),
    add_camera("LB_WHOLE_V219_CAM_FrontEndToTrains", (-7200.0, 1800.0, 1200.0), (1500.0, -1800.0, 350.0), 58.0),
]

failures = []
if not levels.save_current_level():
    failures.append("could not save v219")
protected_after = {key: sha256(path) for key, path in protected.items()}
if protected_before != protected_after:
    failures.append("protected retained source changed")
map_file = protected_file(MAP)
payload = {
    "$schema": "cairnwell/audit/press-shop-whole-shop-automation-preview-build-v219/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_AUTOMATED_TRAINS_INSTALLED_AT_EST-P_PREVIEW_TRANSFORMS__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "map_sha256": sha256(map_file) if map_file.exists() else None,
    "donors": DONORS,
    "protected_sha256_before": protected_before,
    "protected_sha256_after": protected_after,
    "installed_actor_counts": spawned_by_train,
    "restored_hierarchy_edge_count": len(hierarchy_edges),
    "installation": INSTALL,
    "placement_authority": "EST-P_REFERENCE_ONLY__GLOBAL_PRODUCTION_DATUMS_REMAIN_TBC_NOT_INVENTED",
    "control_room_operations_console": "INHERITED__SELECTED_TRAIN_COMMAND_BINDING_REQUIRES_SEPARATE_RUNTIME_GATE",
    "fixed_cameras": cameras,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_WHOLE_SHOP_AUTOMATION_PREVIEW_V219_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
