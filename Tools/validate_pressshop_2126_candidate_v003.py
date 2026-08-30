"""Full structural verification for the fresh, real-Meshy 2126 Press candidate.

This verifies deliberate map-side work after the initial replacement pass:
press provenance, coil policy, real material flow, sparse automation, exact
B_stylized lighting values, camera exposure and protected-map preservation.
It makes no map or asset edits.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
V438 = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V438_SHA256 = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_candidate_validation_v003.json"

PRESSES = {
    "MESHY | S02 Draw / form | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S02_DrawForm_MeshyClean_v001",
    "MESHY | S03 Trim | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "MESHY | S04 Pierce | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "MESHY | S05 Flange / hem | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "MESHY | S06 Vision / outfeed | reused press asset": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
}
ROBOT = "/Game/Meshes/Robot/SM_RoboArm04"
MATERIAL_FLOW = {
    "FLOW | S01-to-S02 real roller handoff": "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/Cairnwell_RollerConveyor_Movable_v740/StaticMeshes/SM_CA_ROLLER_CONVEYO__TEXTURED_STATIC_v740",
    "FLOW | S06 real exit conveyor frame": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001",
    "FLOW | S06 real exit conveyor belt": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001",
}
CAMERAS = ("CAM | 2126 Steam hero overview", "CAM | 2126 operator line", "CAM | 2126 draw nexus")
OLD_PREFIXES = ("S02 Draw Nexus |", "S03 Trim Array |", "S04 Pierce Cell |", "S05 Edge Forge |", "S06 | vision", "S06 | autonomous", "S06 | optical", "transfer | ")


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_VALIDATION_V003_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def mesh_path(actor):
    component = actor.static_mesh_component
    mesh = component.static_mesh
    if not isinstance(mesh, unreal.StaticMesh):
        fail("not a StaticMesh actor: " + actor.get_actor_label())
    return mesh.get_path_name().split(".")[0], mesh


def visible(actor):
    components = actor.get_components_by_class(unreal.PrimitiveComponent)
    return bool(components) and all(component.is_visible() for component in components)


if not V438.is_file() or sha256(V438) != V438_SHA256:
    fail("protected v438 map hash differs from its immutable recorded value")
if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("candidate map missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}

press_rows = []
for label, expected in PRESSES.items():
    actor = by_label.get(label)
    if not isinstance(actor, unreal.StaticMeshActor) or not visible(actor):
        fail("missing or hidden real Meshy press: " + label)
    actual, mesh = mesh_path(actor)
    if actual != expected:
        fail("wrong mesh bound to " + label)
    center, extent = actor.get_actor_bounds(False)
    press_rows.append({"label": label, "center_x_cm": round(center.x, 2), "extent_x_cm": round(extent.x, 2), "triangles_lod0": int(mesh.get_num_triangles(0))})

press_rows.sort(key=lambda row: row["center_x_cm"])
gaps = []
for left, right in zip(press_rows, press_rows[1:]):
    gap = right["center_x_cm"] - right["extent_x_cm"] - left["center_x_cm"] - left["extent_x_cm"]
    if gap < 600.0:
        fail("real press envelopes lack 6m clearance: %s to %s = %.2fcm" % (left["label"], right["label"], gap))
    gaps.append({"between": [left["label"], right["label"]], "clearance_cm": round(gap, 2)})

hidden = [actor.get_actor_label() for actor in actors if actor.get_actor_label().startswith(OLD_PREFIXES) and not visible(actor)]
if len(hidden) < 40:
    fail("first-pass press blockout history is not fully hidden")

coils = [actor.get_actor_label() for actor in actors if unreal.Name("LB.Reused.ProjectCoil") in actor.tags]
if len(coils) != 2:
    fail("candidate must retain exactly two separate project coils")

roof_labels = [actor.get_actor_label() for actor in actors if isinstance(actor, unreal.StaticMeshActor) and "roof" in actor.get_actor_label().lower() and visible(actor)]
if roof_labels:
    fail("roofless candidate has visible roof-labelled mesh: " + ", ".join(roof_labels))

flow_rows = []
for label, expected in MATERIAL_FLOW.items():
    actor = by_label.get(label)
    if not isinstance(actor, unreal.StaticMeshActor) or not visible(actor):
        fail("missing visible real material-flow piece: " + label)
    actual, mesh = mesh_path(actor)
    if actual != expected:
        fail("wrong material-flow mesh bound to " + label)
    flow_rows.append({"label": label, "triangles_lod0": int(mesh.get_num_triangles(0))})
rail_labels = [actor.get_actor_label() for actor in actors if actor.get_actor_label().startswith("FLOW | reused transfer rail ") and visible(actor)]
if len(rail_labels) != 8:
    fail("expected 8 visible real transfer rail spans, found %d" % len(rail_labels))

robots = [actor for actor in actors if actor.get_actor_label().startswith("ROBOT | ") and visible(actor)]
if len(robots) != 4:
    fail("expected exactly 4 sparse visible robot cues")
for actor in robots:
    actual, mesh = mesh_path(actor)
    if actual != ROBOT or int(mesh.get_num_triangles(0)) > 20000:
        fail("robot cue violates reuse or triangle guard: " + actor.get_actor_label())

fixtures = [actor for actor in actors if actor.get_actor_label().startswith("2126 | B_stylized 5000K fixture ")]
if len(fixtures) != 6:
    fail("expected exactly six B_stylized fixtures")
fixture_rows = []
for actor in fixtures:
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None or not component.is_visible() or abs(component.get_editor_property("intensity") - 1200.0) > 0.01 or not component.get_editor_property("use_temperature") or abs(component.get_editor_property("temperature") - 5000.0) > 0.01:
        fail("B_stylized fixture values wrong: " + actor.get_actor_label())
    fixture_rows.append(actor.get_actor_label())
sun = by_label.get("2126 | B_stylized sun")
sky = by_label.get("2126 | B_stylized sky")
if sun is None or sky is None:
    fail("B_stylized sun or sky missing")
if abs(sun.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property("intensity") - 0.30) > 0.001:
    fail("B_stylized sun intensity differs from 0.30")
if abs(sky.get_component_by_class(unreal.SkyLightComponent).get_editor_property("intensity") - 0.20) > 0.001:
    fail("B_stylized sky intensity differs from 0.20")

camera_rows = []
for label in CAMERAS:
    actor = by_label.get(label)
    if actor is None:
        fail("missing review camera " + label)
    camera = actor.get_component_by_class(unreal.CineCameraComponent)
    settings = camera.get_editor_property("post_process_settings")
    if not settings.get_editor_property("override_auto_exposure_bias") or abs(settings.get_editor_property("auto_exposure_bias") + 0.50) > 0.001 or abs(camera.get_editor_property("post_process_blend_weight") - 1.0) > 0.001:
        fail("fixed B_stylized exposure missing from " + label)
    camera_rows.append(label)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__FRESH_2126_CANDIDATE_STRUCTURALLY_ALIGNED_TO_REAL_MESHY_AND_B_STYLIZED_CONTRACT",
    "candidate_map": MAP,
    "candidate_actor_count": len(actors),
    "presses": press_rows,
    "press_envelope_clearance": gaps,
    "hidden_first_pass_blockouts": len(hidden),
    "separate_project_coils": coils,
    "roofless_visible_mesh_check": "PASS",
    "material_flow": flow_rows,
    "visible_real_transfer_rails": len(rail_labels),
    "sparse_reused_robots": [actor.get_actor_label() for actor in robots],
    "B_stylized": {"fixtures": sorted(fixture_rows), "lumens": 1200, "kelvin": 5000, "sun": 0.30, "sky": 0.20, "camera_exposure": -0.50},
    "review_cameras": camera_rows,
    "protected_v438_sha256": sha256(V438),
    "honest_status": "structural validation only; fresh Real-RHI player-view capture and visual acceptance remain required",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_VALIDATION_V003_PASS presses=%d robots=%d rails=%d" % (len(press_rows), len(robots), len(rail_labels)))
