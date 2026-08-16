"""Create non-overwriting B/C identity-readability successors from retained v001.

Only existing presentation material assignments and metadata change.  Runtime,
transforms, collision, navigation and the unplaced local-origin policy are
preserved exactly.
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

variants = {
    "B": {
        "parent": "/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001",
        "parent_hash": "EA511F15D2E70C0FD84560CF8DD8B6909512ED2F051EC1B8230BEAD29BBAA30E",
        "target": "/Game/LineBoss/Maps/LB_PressTrainBVisualReadabilityCandidate_v002",
        "family": "FLOORS / UNDERBODY",
    },
    "C": {
        "parent": "/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001",
        "parent_hash": "1F7282069883B84ECB537A666CE860902BA6B41F316752B4EE17775BA92423F6",
        "target": "/Game/LineBoss/Maps/LB_PressTrainCVisualReadabilityCandidate_v002",
        "family": "CLOSURES",
    },
}

protected = {
    root / "Content/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027.umap":
        "00225848C15668BE523F181FD81A8C1FB472675A724B72847B9E206A7C99848F",
    root / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap":
        "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def actor_tags(actor):
    return {str(value) for value in actor.tags}


def add_tags(actor, *values):
    tags = actor_tags(actor)
    tags.update(values)
    actor.set_editor_property("tags", [unreal.Name(value) for value in sorted(tags)])


for path, expected in protected.items():
    if sha(path) != expected:
        raise RuntimeError(f"protected predecessor changed: {path.name}")

reports = {}
for letter, spec in variants.items():
    parent_file = root / f"Content/LineBoss/Maps/{spec['parent'].rsplit('/', 1)[-1]}.umap"
    target_file = root / f"Content/LineBoss/Maps/{spec['target'].rsplit('/', 1)[-1]}.umap"
    output = root / f"Saved/Audits/PressTrains/press_train_{letter.lower()}_visual_readability_build_v002.json"
    if sha(parent_file) != spec["parent_hash"]:
        raise RuntimeError(f"Train {letter} v001 parent changed")
    if library.does_asset_exist(spec["target"]) or target_file.exists() or output.exists():
        raise RuntimeError(f"refusing to overwrite Train {letter} v002")
    if not levels.new_level_from_template(spec["target"], spec["parent"]):
        raise RuntimeError(f"could not create Train {letter} v002")

    actors = list(actors_api.get_all_level_actors())
    authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
    if len(authorities) != 1:
        raise RuntimeError(f"Train {letter}: authority count {len(authorities)}")
    authority = authorities[0]
    accent_path = (
        f"/Game/LineBoss/Candidates/PressTrains/Variants/Candidate_v001/Materials/"
        f"M_CA_MW_PT_Train{letter}Accent_v001")
    accent = library.load_asset(accent_path)
    if accent is None:
        raise RuntimeError(accent_path)
    rubber = library.load_asset(
        "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/"
        "M_CA_MW_PTA_DarkRubber_AssemblyStudyRobotFamily_v017")
    if rubber is None:
        raise RuntimeError("retained dark-rubber material missing")

    identity_rows = []
    gripper_drop_rows = []
    gripper_pad_rows = []
    transform_before = {}
    for actor in actors:
        location = actor.get_actor_location()
        rotation = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        transform_before[actor.get_actor_label()] = (
            location.x, location.y, location.z,
            rotation.roll, rotation.pitch, rotation.yaw,
            scale.x, scale.y, scale.z)
        tags = actor_tags(actor)
        roles = {value.rsplit(".", 1)[-1] for value in tags if value.startswith("LB.PressTrain.Role.")}
        if isinstance(actor, unreal.StaticMeshActor) and "stage_identity" in roles:
            # Slot 0 is the dark plate body; slot 1 is the inherited green ID
            # accent.  v001 changed only slot 0, leaving Train C visually green.
            # Keep the label-ivory and worked-steel slots intact.
            actor.static_mesh_component.set_material(0, accent)
            if len(actor.static_mesh_component.get_materials()) > 1:
                actor.static_mesh_component.set_material(1, accent)
            add_tags(actor, f"LB.PressTrain.Train{letter}.IdentityReadability.v002")
            identity_rows.append(actor.get_actor_label())
        if letter == "C" and isinstance(actor, unreal.StaticMeshActor) and "transfer_gripper" in roles:
            if "GripperPad" in actor.get_actor_label():
                actor.static_mesh_component.set_material(0, rubber)
                add_tags(actor, "LB.PressTrain.VariantC.FlexibleGripper.ContactPad.v002")
                gripper_pad_rows.append(actor.get_actor_label())
            else:
                actor.static_mesh_component.set_material(0, accent)
                add_tags(actor, "LB.PressTrain.VariantC.FlexibleGripper.DropLink.v002")
                gripper_drop_rows.append(actor.get_actor_label())
        add_tags(actor, f"LB.PressTrain.Train{letter}.VisualReadability.v002")

    if not levels.save_current_level():
        raise RuntimeError(f"Train {letter}: save failed")
    failures = []
    if len(actors) != 366:
        failures.append(f"actor count {len(actors)} != 366")
    if len(identity_rows) != 7:
        failures.append(f"identity count {len(identity_rows)} != 7")
    if letter == "C" and (len(gripper_drop_rows) != 10 or len(gripper_pad_rows) != 10):
        failures.append(
            f"C gripper semantic counts drop={len(gripper_drop_rows)} pad={len(gripper_pad_rows)}")
    if authority.get_train_display_name() != f"TRAIN {letter}":
        failures.append("native train identity changed")
    if authority.get_part_family() != spec["family"]:
        failures.append("native part family changed")
    for actor in actors:
        before = transform_before[actor.get_actor_label()]
        location = actor.get_actor_location(); rotation = actor.get_actor_rotation(); scale = actor.get_actor_scale3d()
        after = (location.x, location.y, location.z, rotation.roll, rotation.pitch, rotation.yaw,
                 scale.x, scale.y, scale.z)
        if any(abs(a - b) > 0.0001 for a, b in zip(before, after)):
            failures.append(f"transform changed: {actor.get_actor_label()}")
            break
    report = {
        "$schema": f"cairnwell/audit/press-train-{letter.lower()}-visual-readability-build-v002/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__VISUAL_READABILITY_SUCCESSOR__PIE_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
            if not failures else "FAIL__NOT_PROMOTED",
        "parent_map": spec["parent"], "parent_sha256": spec["parent_hash"],
        "target_map": spec["target"], "target_sha256": sha(target_file),
        "actor_count": len(actors), "identity_plate_count": len(identity_rows),
        "gripper_drop_link_count": len(gripper_drop_rows),
        "gripper_contact_pad_count": len(gripper_pad_rows),
        "transform_changes": 0 if not any("transform changed" in value for value in failures) else 1,
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
