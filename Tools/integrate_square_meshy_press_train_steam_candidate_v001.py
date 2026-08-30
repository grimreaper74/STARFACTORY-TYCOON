"""Place the five cleaned square-style candidate presses into the v438-derived Steam scene.

This script deliberately edits only the new Steam candidate clone.  It keeps the
protected v438 map byte-identical, hides rather than deletes the superseded
Train-A visual presentation, and makes the bare/wrapped project coil assets
independent actors rather than geometry embedded in a generated press.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
PROTECTED_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "square_meshy_press_train_steam_placement_v001.json"
TAG = unreal.Name("LB.PressShop.SquareMeshy.SteamCandidate.v001")
REPLACED_TAG = unreal.Name("LB.PressShop.SquareMeshy.SupersededVisual.v001")

ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
MATERIAL_ROOT = ROOT + "/Materials"
PRESS = {
    # All source-heading compensation is inherited from the isolated review
    # pass.  This produces one continuous +Y material path and retains the
    # project convention of the operator facade on -X.
    "S02 Draw/Form": (ROOT + "/SM_LB_PS_S02_DrawForm_MeshyClean_v001", (3850.0, -2700.0, 0.0), 90.0),
    "S03 Trim": (ROOT + "/SM_LB_PS_S03_Trim_MeshyClean_v001", (3850.0, -685.0, 0.0), 180.0),
    "S04 Pierce": (ROOT + "/SM_LB_PS_S04_Pierce_MeshyClean_v001", (3850.0, 1028.0, 0.0), 90.0),
    "S05 Flange/Hem": (ROOT + "/SM_LB_PS_S05_FlangeHem_MeshyClean_v001", (3850.0, 2681.0, 0.0), 180.0),
    "S06 Vision/Outfeed": (ROOT + "/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001", (3850.0, 4467.0, 0.0), 180.0),
}
COILS = {
    "Bare project coil - separate": "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021",
    "Wrapped project coil - separate": "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003",
}
CONVEYOR_FRAME = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001"
CONVEYOR_BELT = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001"
CONTEXT = {
    "S01 Decoiler base - reused": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerBase_v001",
    "S01 Decoiler spindle - reused": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerSpindle_v001",
    "S01 Straightener feed - reused": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01StraightenerFeed_v001",
    "S01 Feed bridge - reused": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01FeedBridge_v001",
    "S07 Inspection cell - reused": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07InspectionCell_v001",
}

# These are old candidate train representations in the Train-A-to-D grid.  A
# Steam candidate must not double-draw the old train and the new line, but this
# transition is reversible: only visibility is changed, never destruction.
HIDE_LABELS = (
    "LB_V300_PTA_SEGMENTED_BALANCED_SHELL",
    "CA_MW_PTA_v040_RELEASE_VISUAL_SUBSTRATE_v343",
    "CA_MW_PTA_v046_PRO_DETAIL_VISUAL_ONLY_v354",
    "CA_MW_PTB_v049_PRO_DETAIL_LAYOUT_PREVIEW_v356",
    "CA_MW_PTC_v049_PRO_DETAIL_LAYOUT_PREVIEW_v356",
    "CA_MW_PTD_v049_PRO_DETAIL_LAYOUT_PREVIEW_v356",
    "LB_V429_TRAIN_A_PHYSICAL_IDENTITY_BOARD",
    "LB_V429_TRAIN_A_DYNAMIC_ALLOCATED_LABEL",
    "LB_V429_TRAIN_B_PHYSICAL_IDENTITY_BOARD",
    "LB_V429_TRAIN_B_DYNAMIC_ALLOCATED_LABEL",
    "LB_V429_TRAIN_C_PHYSICAL_IDENTITY_BOARD",
    "LB_V429_TRAIN_C_DYNAMIC_ALLOCATED_LABEL",
    "LB_V429_TRAIN_D_PHYSICAL_IDENTITY_BOARD",
    "LB_V429_TRAIN_D_DYNAMIC_ALLOCATED_LABEL",
)


def fail(message):
    raise RuntimeError("SQUARE_MESHY_STEAM_PLACEMENT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_actor(label, mesh, location, yaw, extra_tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0),
    )
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.Asset.Candidate"), unreal.Name("LB.NotProcessWIP")] + list(extra_tags)
    actor.static_mesh_component.set_static_mesh(mesh)
    return actor


def actor_by_label(actors, label):
    matching = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matching) != 1:
        fail("expected exactly one old actor named %s, found %d" % (label, len(matching)))
    return matching[0]


if not PROTECTED_FILE.is_file():
    fail("protected v438 source map is missing")
protected_hash_before = sha256(PROTECTED_FILE)
if not unreal.EditorAssetLibrary.does_asset_exist(CANDIDATE):
    fail("new Steam candidate map is missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(CANDIDATE):
    fail("could not load Steam candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("Steam candidate already contains this placement tag; refusing to duplicate the press line")

assets = {}
for label, (path, _, _) in PRESS.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing press static mesh: " + label)
    assets[label] = asset
for label, path in COILS.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing approved project coil: " + label)
    assets[label] = asset
for label, path in CONTEXT.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing approved native context mesh: " + label)
    assets[label] = asset
frame_mesh = unreal.load_asset(CONVEYOR_FRAME)
belt_mesh = unreal.load_asset(CONVEYOR_BELT)
if not isinstance(frame_mesh, unreal.StaticMesh) or not isinstance(belt_mesh, unreal.StaticMesh):
    fail("approved native conveyor meshes are unavailable")

# Hide the superseded visual cells without deleting their evidence.  Primitive
# visibility is persisted in the clone so normal editor and game views agree.
hidden = []
for label in HIDE_LABELS:
    old_actor = actor_by_label(actors, label)
    old_actor.set_actor_hidden_in_game(True)
    old_actor.tags = list(old_actor.tags) + [REPLACED_TAG]
    for component in old_actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)
    hidden.append(label)

placed = []
for label, (_, location, yaw) in PRESS.items():
    actor = make_actor(label + " - new square-style candidate", assets[label], location, yaw, (unreal.Name("LB.PressShop.NewPressLine"),))
    placed.append({"label": actor.get_actor_label(), "asset": assets[label].get_path_name(), "location_cm": list(location), "yaw": yaw})

# Reuse the project's roller/belt pieces in the generous hand-off gaps.  No
# new generated roller geometry is introduced.  A belt and frame remain
# separate, meaning the belt can later receive a material-scroll mechanism.
green = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_CairnwellGreen")
charcoal = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_FoundryCharcoal")
steel = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_SteelGrey")
yellow = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_SafetyYellow")
if any(material is None for material in (green, charcoal, steel, yellow)):
    fail("candidate palette materials are unavailable")
for index, y in enumerate((-1673.0, 303.0, 1754.0, 3575.0), start=1):
    frame = make_actor("Reused native transfer conveyor frame %02d" % index, frame_mesh, (3850.0, y, 0.0), 0.0, (unreal.Name("LB.PressShop.ReusedConveyor"),))
    for slot, material in enumerate((green, charcoal, steel, steel, yellow, green)):
        frame.static_mesh_component.set_material(slot, material)
    belt = make_actor("Reused native transfer conveyor belt %02d" % index, belt_mesh, (3850.0, y, 0.0), 0.0, (unreal.Name("LB.PressShop.ReusedConveyor"),))
    belt.static_mesh_component.set_material(0, charcoal)
    placed.append({"label": frame.get_actor_label(), "asset": frame_mesh.get_path_name(), "location_cm": [3850.0, y, 0.0], "yaw": 0.0})
    placed.append({"label": belt.get_actor_label(), "asset": belt_mesh.get_path_name(), "location_cm": [3850.0, y, 0.0], "yaw": 0.0})

# Build the inlet from existing native context assets.  The coils are visibly
# separate project actors: bare coil in the live intake zone, wrapped coil in
# its neighbouring receiving position.  Neither is attached to a Meshy mesh.
for label, location in (
    ("S01 Decoiler base - reused", (3850.0, -5000.0, 0.0)),
    ("S01 Decoiler spindle - reused", (3850.0, -5000.0, 0.0)),
    ("S01 Straightener feed - reused", (3850.0, -4550.0, 0.0)),
    ("S01 Feed bridge - reused", (3850.0, -4000.0, 0.0)),
    ("S07 Inspection cell - reused", (3850.0, 5220.0, 0.0)),
    ("Bare project coil - separate", (4800.0, -5000.0, 0.0)),
    ("Wrapped project coil - separate", (5250.0, -4550.0, 0.0)),
):
    actor = make_actor(label, assets[label], location, 0.0, (unreal.Name("LB.PressShop.NativeContext"),))
    placed.append({"label": actor.get_actor_label(), "asset": assets[label].get_path_name(), "location_cm": list(location), "yaw": 0.0})

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save the Steam candidate map")
protected_hash_after = sha256(PROTECTED_FILE)
if protected_hash_before != protected_hash_after:
    fail("protected v438 source map changed while candidate was being edited")

report = {
    "status": "PASS__NEW_SQUARE_MESHY_PRESS_LINE_PLACED_IN_STEAM_CANDIDATE_ONLY",
    "candidate": CANDIDATE,
    "protected_v438_sha256_before": protected_hash_before,
    "protected_v438_sha256_after": protected_hash_after,
    "hidden_not_deleted_old_visuals": hidden,
    "new_candidate_actors": placed,
    "orientation": {"material_flow": "+Y", "operator_facade": "-X"},
    "coil_policy": "bare and wrapped project coils are separate actors; no coil is embedded in a generated press",
    "conveyor_policy": "four native project frame/belt pairs are reused between stations; no raw Meshy rollers were created",
    "next_gate": "open the candidate in the full Unreal editor, visually inspect all five placements, then build only the lighting and camera evidence that the inspection proves necessary",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("SQUARE_MESHY_STEAM_PLACEMENT=" + json.dumps({"hidden": len(hidden), "placed": len(placed)}, sort_keys=True))
