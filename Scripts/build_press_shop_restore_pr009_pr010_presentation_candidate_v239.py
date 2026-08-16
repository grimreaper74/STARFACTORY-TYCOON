"""Restore accepted PR009/PR010 presentation into a fresh v236 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236"
DONOR = "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_restore_pr009_pr010_presentation_build_v239.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236.umap"
DONOR_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR010Accepted_v103.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239.umap"
TOKENS = {"PR009": "LB.Asset.Accepted.PR009.v096", "PR010": "LB.Asset.Accepted.PR010.v103"}
EXPECTED = {
    "PR009": {"StaticMeshActor": 201, "TextRenderActor": 6, "RectLight": 2},
    "PR010": {"StaticMeshActor": 250, "TextRenderActor": 47, "PointLight": 4},
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
    return {"location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation()),
            "scale": vec(actor.get_actor_scale3d())}


def make_transform(record):
    return unreal.Transform(location=unreal.Vector(*record["location"]),
                            rotation=unreal.Rotator(*record["rotation"]),
                            scale=unreal.Vector(*record["scale"]))


if not levels.load_level(DONOR):
    raise RuntimeError(f"could not load accepted donor {DONOR}")
donor_hash_before = sha256(DONOR_FILE)
records = {key: [] for key in TOKENS}
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    station = next((key for key, token in TOKENS.items() if token in tags), None)
    if station is None:
        continue
    common = {
        "station": station,
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "transform": transform_record(actor),
        "tags": tags,
        "parent": actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else None,
    }
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        mesh = prop(component, "static_mesh")
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"accepted donor mesh missing on {common['label']}")
        common.update({
            "mesh": mesh.get_path_name(),
            "materials": [component.get_material(index).get_path_name() if component.get_material(index) else None
                          for index in range(component.get_num_materials())],
            "collision_enabled": component.get_collision_enabled(),
            "collision_profile": component.get_collision_profile_name(),
            "affects_navigation": bool(prop(component, "can_ever_affect_navigation", False)),
            "cast_shadow": bool(prop(component, "cast_shadow", True)),
            "visible": bool(prop(component, "visible", True)),
            "mobility": prop(component, "mobility"),
        })
    elif isinstance(actor, unreal.TextRenderActor):
        component = actor.text_render
        common.update({
            "text": str(prop(component, "text", "")),
            "world_size": float(prop(component, "world_size", 24.0)),
            "color": prop(component, "text_render_color", unreal.Color(220, 235, 225, 255)),
            "horizontal_alignment": prop(component, "horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER),
            "vertical_alignment": prop(component, "vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER),
            "collision_enabled": component.get_collision_enabled(),
            "affects_navigation": bool(prop(component, "can_ever_affect_navigation", False)),
            "visible": bool(prop(component, "visible", True)),
        })
    elif isinstance(actor, unreal.RectLight):
        component = actor.rect_light_component
        common.update({
            "intensity": float(prop(component, "intensity", 0.0)),
            "light_color": prop(component, "light_color", unreal.Color(255, 255, 255, 255)),
            "attenuation_radius": float(prop(component, "attenuation_radius", 1000.0)),
            "source_width": float(prop(component, "source_width", 64.0)),
            "source_height": float(prop(component, "source_height", 64.0)),
            "cast_shadows": bool(prop(component, "cast_shadows", True)),
            "visible": bool(prop(component, "visible", True)),
        })
    elif isinstance(actor, unreal.PointLight):
        component = actor.point_light_component
        common.update({
            "intensity": float(prop(component, "intensity", 0.0)),
            "light_color": prop(component, "light_color", unreal.Color(255, 255, 255, 255)),
            "attenuation_radius": float(prop(component, "attenuation_radius", 1000.0)),
            "source_radius": float(prop(component, "source_radius", 0.0)),
            "soft_source_radius": float(prop(component, "soft_source_radius", 0.0)),
            "source_length": float(prop(component, "source_length", 0.0)),
            "cast_shadows": bool(prop(component, "cast_shadows", True)),
            "visible": bool(prop(component, "visible", True)),
        })
    else:
        continue
    records[station].append(common)

source_counts = {station: {name: sum(row["class"] == name for row in rows)
                           for name in EXPECTED[station]}
                 for station, rows in records.items()}
if source_counts != EXPECTED:
    raise RuntimeError(f"accepted donor contract mismatch expected={EXPECTED} actual={source_counts}")

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

existing_labels = {actor.get_actor_label() for actor in actors_api.get_all_level_actors()}
label_conflicts = sorted(row["label"] for rows in records.values() for row in rows if row["label"] in existing_labels)
if label_conflicts:
    raise RuntimeError(f"accepted presentation labels already present: {label_conflicts[:10]}")

spawned = {}
created = []
failures = []
for station in ("PR009", "PR010"):
    for record in records[station]:
        actor_class = {
            "StaticMeshActor": unreal.StaticMeshActor,
            "TextRenderActor": unreal.TextRenderActor,
            "RectLight": unreal.RectLight,
            "PointLight": unreal.PointLight,
        }[record["class"]]
        actor = actors_api.spawn_actor_from_class(actor_class, unreal.Vector(), unreal.Rotator())
        if actor is None:
            failures.append(f"could not spawn {record['label']}")
            continue
        actor.set_actor_label(record["label"])
        actor.set_actor_transform(make_transform(record["transform"]), False, True)
        actor.tags = [unreal.Name(value) for value in dict.fromkeys(record["tags"] + [
            "LB.Integration.WholeShop.RestoredAcceptedPresentation.v239",
            "LB.Asset.Candidate.v239", "LB.Asset.CandidateNotPromoted"])]
        if record["class"] == "StaticMeshActor":
            component = actor.static_mesh_component
            mesh = library.load_asset(record["mesh"])
            if not isinstance(mesh, unreal.StaticMesh):
                failures.append(f"missing accepted mesh {record['mesh']}")
                actors_api.destroy_actor(actor)
                continue
            component.set_static_mesh(mesh)
            for index, material_path in enumerate(record["materials"]):
                if material_path:
                    material = library.load_asset(material_path)
                    if material is None:
                        failures.append(f"missing accepted material {material_path}")
                        continue
                    component.set_material(index, material)
            component.set_collision_enabled(record["collision_enabled"])
            component.set_collision_profile_name(record["collision_profile"])
            component.set_editor_property("can_ever_affect_navigation", record["affects_navigation"])
            component.set_editor_property("cast_shadow", record["cast_shadow"])
            component.set_editor_property("visible", record["visible"])
            component.set_mobility(record["mobility"])
        elif record["class"] == "TextRenderActor":
            component = actor.text_render
            component.set_text(record["text"])
            component.set_world_size(record["world_size"])
            component.set_text_render_color(record["color"])
            component.set_horizontal_alignment(record["horizontal_alignment"])
            component.set_vertical_alignment(record["vertical_alignment"])
            component.set_collision_enabled(record["collision_enabled"])
            component.set_editor_property("can_ever_affect_navigation", record["affects_navigation"])
            component.set_editor_property("visible", record["visible"])
        elif record["class"] == "RectLight":
            component = actor.rect_light_component
            component.set_editor_properties({
                "intensity": record["intensity"], "light_color": record["light_color"],
                "attenuation_radius": record["attenuation_radius"],
                "source_width": record["source_width"], "source_height": record["source_height"],
                "cast_shadows": record["cast_shadows"], "visible": record["visible"],
            })
        elif record["class"] == "PointLight":
            component = actor.point_light_component
            component.set_editor_properties({
                "intensity": record["intensity"], "light_color": record["light_color"],
                "attenuation_radius": record["attenuation_radius"],
                "source_radius": record["source_radius"],
                "soft_source_radius": record["soft_source_radius"],
                "source_length": record["source_length"],
                "cast_shadows": record["cast_shadows"], "visible": record["visible"],
            })
        spawned[record["label"]] = actor
        created.append({"station": station, "label": record["label"], "class": record["class"]})

for station in ("PR009", "PR010"):
    for record in records[station]:
        if not record["parent"]:
            continue
        child = spawned.get(record["label"])
        parent_actor = spawned.get(record["parent"])
        if child is not None and parent_actor is not None:
            if not child.attach_to_actor(parent_actor, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
                                         unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
                failures.append(f"could not restore hierarchy {record['label']}->{record['parent']}")

created_counts = {station: {name: sum(row["station"] == station and row["class"] == name for row in created)
                            for name in EXPECTED[station]}
                  for station in EXPECTED}
if created_counts != EXPECTED:
    failures.append(f"created contract mismatch expected={EXPECTED} actual={created_counts}")

authorities = {"PR009": 0, "PR010": 0}
for actor in actors_api.get_all_level_actors():
    name = actor.get_class().get_name()
    if name == "LBPR009Station":
        authorities["PR009"] += 1
    elif name == "LBPR010Station":
        authorities["PR010"] += 1
if authorities != {"PR009": 1, "PR010": 1}:
    failures.append(f"native authority cardinality changed {authorities}")

if not levels.save_current_level():
    failures.append("could not save v239")
parent_hash_after = sha256(BASE_FILE)
donor_hash_after = sha256(DONOR_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v236 parent changed")
if donor_hash_after != donor_hash_before:
    failures.append("accepted v103 donor changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-restore-pr009-pr010-presentation-build-v239/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ACCEPTED_PR009_PR010_PRESENTATION_RESTORED__FRESH_VISUAL_RUNTIME_COLLISION_NAVIGATION_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "donor": DONOR,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "donor_hash_before": donor_hash_before,
    "donor_hash_after": donor_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "source_counts": source_counts,
    "created_counts": created_counts,
    "created_actor_count": len(created),
    "native_authorities": authorities,
    "new_native_authorities": 0,
    "invented_dimensions_or_datums": 0,
    "accepted_transform_material_collision_navigation_contract_replayed": True,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
