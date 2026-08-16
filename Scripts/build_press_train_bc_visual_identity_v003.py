"""Add restrained, readable two-layer operator-side identity plates to B/C.

v002 proved that changing hidden/overexposed source material slots alone did
not survive the fixed camera.  This successor starts again from retained v001
and adds only NoCollision presentation actors at the existing stage-identity
datums.  No machine transform, runtime binding or world placement changes.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
charcoal = library.load_asset(
    "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/"
    "M_CA_MW_PTA_Charcoal_AssemblyStudyRobotFamily_v017")
if cube is None or charcoal is None:
    raise RuntimeError("retained identity construction assets missing")

variants = {
    "B": {
        "parent": "/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001",
        "parent_hash": "EA511F15D2E70C0FD84560CF8DD8B6909512ED2F051EC1B8230BEAD29BBAA30E",
        "target": "/Game/LineBoss/Maps/LB_PressTrainBVisualIdentityCandidate_v003",
        "family": "FLOORS / UNDERBODY",
    },
    "C": {
        "parent": "/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001",
        "parent_hash": "1F7282069883B84ECB537A666CE860902BA6B41F316752B4EE17775BA92423F6",
        "target": "/Game/LineBoss/Maps/LB_PressTrainCVisualIdentityCandidate_v003",
        "family": "CLOSURES",
    },
}
stage_names = {
    "S01": "DESTACK", "S02": "DRAW", "S03": "FORM", "S04": "TRIM",
    "S05": "PIERCE", "S06": "FLANGE", "S07": "UNLOAD",
}
protected = {
    root / "Content/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027.umap":
        "00225848C15668BE523F181FD81A8C1FB472675A724B72847B9E206A7C99848F",
    root / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap":
        "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def tags(actor):
    return {str(value) for value in actor.tags}


def stage_of(actor):
    values = [value.rsplit(".", 1)[-1] for value in tags(actor)
              if value.startswith("LB.PressTrain.Stage.S")]
    return values[0] if len(values) == 1 else None


def set_presentation(component):
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)


for path, expected in protected.items():
    if sha(path) != expected:
        raise RuntimeError(f"protected predecessor changed: {path.name}")

reports = {}
for letter, spec in variants.items():
    parent_file = root / f"Content/LineBoss/Maps/{spec['parent'].rsplit('/', 1)[-1]}.umap"
    target_file = root / f"Content/LineBoss/Maps/{spec['target'].rsplit('/', 1)[-1]}.umap"
    output = root / f"Saved/Audits/PressTrains/press_train_{letter.lower()}_visual_identity_build_v003.json"
    if sha(parent_file) != spec["parent_hash"]:
        raise RuntimeError(f"Train {letter} v001 parent changed")
    if library.does_asset_exist(spec["target"]) or target_file.exists() or output.exists():
        raise RuntimeError(f"refusing to overwrite Train {letter} v003")
    if not levels.new_level_from_template(spec["target"], spec["parent"]):
        raise RuntimeError(f"could not create Train {letter} v003")

    inherited = list(actors_api.get_all_level_actors())
    inherited_transforms = {}
    for actor in inherited:
        location = actor.get_actor_location(); rotation = actor.get_actor_rotation(); scale = actor.get_actor_scale3d()
        inherited_transforms[actor.get_actor_label()] = (
            location.x, location.y, location.z, rotation.roll, rotation.pitch, rotation.yaw,
            scale.x, scale.y, scale.z)
    authorities = [actor for actor in inherited if isinstance(actor, unreal.LBPressTrainAStation)]
    identities = [actor for actor in inherited if "LB.PressTrain.Role.stage_identity" in tags(actor)]
    if len(authorities) != 1 or len(identities) != 7:
        raise RuntimeError(f"Train {letter}: authority={len(authorities)} identities={len(identities)}")
    accent = library.load_asset(
        f"/Game/LineBoss/Candidates/PressTrains/Variants/Candidate_v001/Materials/"
        f"M_CA_MW_PT_Train{letter}Accent_v001")
    if accent is None:
        raise RuntimeError(f"Train {letter} accent missing")

    created = []
    for identity in sorted(identities, key=lambda value: value.get_actor_location().y):
        stage = stage_of(identity)
        if stage not in stage_names:
            raise RuntimeError(f"Train {letter}: unresolved stage for {identity.get_actor_label()}")
        anchor = identity.get_actor_location()
        common_tags = [
            unreal.Name("LB.Asset.Candidate.v003"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
            unreal.Name("LB.Authority.WorldPlacement.TBCNotInvented"),
            unreal.Name(f"LB.PressTrain.Train{letter}.VisualIdentity.v003"),
            unreal.Name(f"LB.PressTrain.Stage.{stage}"),
        ]

        outer = actors_api.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(452.0, anchor.y, anchor.z), unreal.Rotator())
        outer.set_actor_label(f"PT{letter}_{stage}_IdentityOuter_v003")
        outer.tags = common_tags + [unreal.Name("LB.PressTrain.Role.variant_identity_backplate")]
        outer.static_mesh_component.set_static_mesh(cube)
        outer.static_mesh_component.set_material(0, charcoal)
        outer.set_actor_scale3d(unreal.Vector(0.035, 2.20, 0.56))
        set_presentation(outer.static_mesh_component)
        created.append(outer)

        insert = actors_api.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(456.0, anchor.y, anchor.z), unreal.Rotator())
        insert.set_actor_label(f"PT{letter}_{stage}_IdentityAccent_v003")
        insert.tags = common_tags + [unreal.Name("LB.PressTrain.Role.variant_identity_accent")]
        insert.static_mesh_component.set_static_mesh(cube)
        insert.static_mesh_component.set_material(0, accent)
        insert.set_actor_scale3d(unreal.Vector(0.025, 2.02, 0.42))
        set_presentation(insert.static_mesh_component)
        created.append(insert)

        text = actors_api.spawn_actor_from_class(
            unreal.TextRenderActor, unreal.Vector(459.0, anchor.y, anchor.z), unreal.Rotator(yaw=0.0))
        text.set_actor_label(f"PT{letter}_{stage}_IdentityText_v003")
        text.tags = common_tags + [unreal.Name("LB.PressTrain.Role.variant_identity_text")]
        component = text.text_render
        component.set_text(f"TRAIN {letter} | PT{letter}-{stage} | {stage_names[stage]}\n{spec['family']}")
        component.set_world_size(11.5)
        component.set_text_render_color(unreal.Color(246, 244, 228, 255))
        component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        component.set_editor_property("cast_shadow", False)
        set_presentation(component)
        created.append(text)

    if not levels.save_current_level():
        raise RuntimeError(f"Train {letter}: save failed")
    failures = []
    actors = list(actors_api.get_all_level_actors())
    if len(actors) != 387:
        failures.append(f"actor count {len(actors)} != 387")
    if len(created) != 21:
        failures.append(f"created count {len(created)} != 21")
    for actor in inherited:
        before = inherited_transforms[actor.get_actor_label()]
        location = actor.get_actor_location(); rotation = actor.get_actor_rotation(); scale = actor.get_actor_scale3d()
        after = (location.x, location.y, location.z, rotation.roll, rotation.pitch, rotation.yaw,
                 scale.x, scale.y, scale.z)
        if any(abs(a - b) > 0.0001 for a, b in zip(before, after)):
            failures.append(f"inherited transform changed: {actor.get_actor_label()}")
            break
    authority = authorities[0]
    if authority.get_train_display_name() != f"TRAIN {letter}" or authority.get_part_family() != spec["family"]:
        failures.append("native identity changed")
    if any(actor.static_mesh_component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION
           for actor in created if isinstance(actor, unreal.StaticMeshActor)):
        failures.append("created plate collision is not NoCollision")
    report = {
        "$schema": f"cairnwell/audit/press-train-{letter.lower()}-visual-identity-build-v003/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__OPERATOR_SIDE_IDENTITY_PLATES__PIE_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
            if not failures else "FAIL__NOT_PROMOTED",
        "parent_map": spec["parent"], "parent_sha256": spec["parent_hash"],
        "target_map": spec["target"], "target_sha256": sha(target_file),
        "inherited_actor_count": len(inherited), "created_visual_actor_count": len(created),
        "final_actor_count": len(actors), "created_collision_policy": "NoCollision",
        "inherited_transform_changes": 0 if not any("transform changed" in value for value in failures) else 1,
        "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
        "promotion_authorized": False, "failures": failures,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    reports[letter] = report
    if failures:
        raise RuntimeError(f"Train {letter}: {'; '.join(failures)}")

for path, expected in protected.items():
    if sha(path) != expected:
        raise RuntimeError(f"protected predecessor changed after build: {path.name}")
print(json.dumps({letter: {"status": row["status"], "hash": row["target_sha256"]}
                  for letter, row in reports.items()}, indent=2))
