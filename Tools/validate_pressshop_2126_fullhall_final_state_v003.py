"""Fail-closed final-state audit for the isolated Cairnwell 2126 Press Shop."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
SEQUENCE = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sequences/LS_CA_MW_2126_PressShopAutomationLoop_v001"
COIL_MESH = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Meshes/SM_CA_MW_2126_MasterCoil_Nanite_v001.SM_CA_MW_2126_MasterCoil_Nanite_v001"
ZONE_MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Materials/M_CA_MW_2126_ProcessZonePaleGreen_Unlit_v001.M_CA_MW_2126_ProcessZonePaleGreen_Unlit_v001"
PALLET_MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites/M_CA_MW_2126_FinishedPanelHoverPallet_UnlitMasked_v001.M_CA_MW_2126_FinishedPanelHoverPallet_UnlitMasked_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullhall_final_state_v003.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
REQUIRED = (
    "2126 LOG | autonomous coil delivery carrier",
    "2126 LOG | autonomous coil unload gantry",
    "2126 COIL | autonomous verification and de-banding cell",
    "2126 COIL | magnetic three-position buffer shuttle",
    "2126 FRONT END | autonomous decoiler straightener and servo feed",
    "2126 PRESS | S01 autonomous deep-draw servo press",
    "2126 PRESS | S02 autonomous redraw calibration press",
    "2126 PRESS | S03 autonomous trim pierce press",
    "2126 PRESS | S04 autonomous flange final-form press",
    "2126 TRANSFER | magnetic panel shuttle sprite 1",
    "2126 TRANSFER | magnetic panel shuttle sprite 2",
    "2126 TRANSFER | magnetic panel shuttle sprite 3",
    "2126 OUTBOUND | AI inspection and metrology cell",
    "2126 OUTBOUND | robotic finished-panel palletisation cell",
    "2126 AUTOMATION | press-shop material-flow loop",
    "CAM | 2126 full hall fixed game view",
)
COILS = (
    "2126 LOG | delivery coil 02 | approved packaged master coil",
    "2126 LOG | delivery coil 03 | approved packaged master coil",
    "2126 LOG | delivery coil 04 | approved packaged master coil",
    "2126 LOG | coil 01 mid-transfer under autonomous gantry",
    "2126 COIL | verification cell active load",
    "2126 COIL | magnetic buffer load A",
    "2126 COIL | magnetic buffer load C",
    "2126 FRONT END | active feed coil",
)
PROCESS_FIELDS = (
    "2126 FLOOR | raw-coil receiving bay pale-green field",
    "2126 FLOOR | coil verification buffer bay pale-green field",
    "2126 FLOOR | servo feed bay pale-green field",
    "2126 FLOOR | continuous pale-green press zone",
    "2126 FLOOR | vision palletisation bay pale-green field",
    "2126 OUTBOUND | pale-green magnetic pallet dispatch lane",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def close(actual, expected, tolerance=0.001):
    return math.isclose(float(actual), float(expected), abs_tol=tolerance)


def fail(message):
    raise RuntimeError(message)


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        fail("protected authority changed: " + str(path))
if OUT.exists():
    fail("refusing to overwrite final-state evidence")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load isolated FullHall candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
missing = [label for label in REQUIRED if label not in by_label]
if missing:
    fail("required process actors missing: " + repr(missing))

legacy_prefixes = ("LB_INST_PTA_", "LB_INST_PTB_", "LB_INST_PTC_", "LB_INST_PTD_")
legacy = [label for label in by_label if label.startswith(legacy_prefixes)]
if legacy:
    fail("inherited press-train actors remain: " + repr(legacy[:10]))

collision_labels = sorted(label for label in by_label if label.startswith("2126 COLLISION |"))
if len(collision_labels) != 11:
    fail("expected 11 native collision proxies, found %d" % len(collision_labels))

coil_rows = []
for label in COILS:
    actor = by_label.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("separate 3D coil actor missing: " + label)
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != COIL_MESH:
        fail("coil not using candidate-local Nanite asset: " + label)
    if component.get_editor_property("cast_shadow"):
        fail("coil shadow-balancing contract changed: " + label)
    coil_rows.append({"label": label, "mesh": mesh.get_path_name(), "material_slots": component.get_num_materials()})

zone_rows = []
for label in PROCESS_FIELDS:
    actor = by_label.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("process field missing: " + label)
    material = actor.static_mesh_component.get_material(0)
    actual = material.get_path_name() if material else None
    if actual != ZONE_MATERIAL:
        fail("process field palette material changed: " + label + " => " + repr(actual))
    zone_rows.append(label)

pallet_rows = []
for slot in ("A", "B", "C"):
    base_label = f"2126 OUTBOUND | hover pallet {slot} collision base"
    card_label = f"2126 OUTBOUND | detailed finished-panel hover pallet sprite {slot}"
    base = by_label.get(base_label)
    card = by_label.get(card_label)
    if not isinstance(base, unreal.StaticMeshActor) or not isinstance(card, unreal.StaticMeshActor):
        fail("detailed hover-pallet pair missing for slot " + slot)
    parent = card.get_attach_parent_actor()
    if parent is None or parent.get_actor_label() != base_label:
        fail("detailed hover-pallet visual detached for slot " + slot)
    material = card.static_mesh_component.get_material(0)
    if material is None or material.get_path_name() != PALLET_MATERIAL:
        fail("detailed hover-pallet material changed for slot " + slot)
    collision_state = str(card.static_mesh_component.get_collision_enabled())
    if "NO_COLLISION" not in collision_state.upper():
        fail("visual card unexpectedly owns collision for slot " + slot + ": " + collision_state)
    pallet_rows.append({"slot": slot, "base": base_label, "card": card_label, "visual_collision": collision_state})

fixtures = [by_label.get("2126 LIGHT | B_stylized fixture %02d" % index) for index in range(1, 7)]
if not all(isinstance(actor, unreal.RectLight) for actor in fixtures):
    fail("approved six-fixture B_stylized rig incomplete")
for actor in fixtures:
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if not close(component.get_editor_property("intensity"), 1200.0, 0.01):
        fail("B_stylized fixture intensity changed: " + actor.get_actor_label())
    if not component.get_editor_property("use_temperature") or not close(component.get_editor_property("temperature"), 5000.0, 0.01):
        fail("B_stylized fixture temperature changed: " + actor.get_actor_label())

sun = by_label.get("2126 LIGHT | B_stylized sun")
sky = by_label.get("2126 LIGHT | B_stylized sky")
volume = by_label.get("2126 LIGHT | fixed Steam exposure")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight) or not isinstance(volume, unreal.PostProcessVolume):
    fail("B_stylized sun, sky or fixed exposure missing")
if not close(sun.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property("intensity"), 0.30):
    fail("B_stylized sun intensity changed")
if not close(sky.get_component_by_class(unreal.SkyLightComponent).get_editor_property("intensity"), 0.20):
    fail("B_stylized sky intensity changed")
settings = volume.get_editor_property("settings")
if not volume.get_editor_property("unbound") or not settings.override_auto_exposure_bias or not close(settings.auto_exposure_bias, -0.50):
    fail("fixed B_stylized exposure changed")

camera = by_label["CAM | 2126 full hall fixed game view"]
if not isinstance(camera, unreal.CameraActor):
    fail("fixed game camera class changed")
rotation = camera.get_actor_rotation()
camera_component = camera.get_component_by_class(unreal.CameraComponent)
if not close(rotation.pitch, -60.0, 0.05) or not close(rotation.yaw, 57.63, 0.05):
    fail("fixed sprite angle changed")
if camera_component.get_editor_property("projection_mode") != unreal.CameraProjectionMode.ORTHOGRAPHIC:
    fail("fixed game camera is no longer orthographic")

sequence = unreal.load_asset(SEQUENCE)
if not isinstance(sequence, unreal.LevelSequence):
    fail("native automation Level Sequence missing")
bindings = list(sequence.get_bindings())
if len(bindings) != 19:
    fail("native automation binding count changed: %d" % len(bindings))

active_lights = []
legacy_disabled = 0
for actor in actors:
    if not isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight, unreal.RectLight, unreal.PointLight, unreal.SpotLight)):
        continue
    components = actor.get_components_by_class(unreal.LightComponent)
    visible = any(component.is_visible() for component in components)
    if visible and not bool(actor.get_editor_property("hidden")):
        active_lights.append(actor.get_actor_label())
    elif unreal.Name("LB.LegacyLighting.Disabled") in actor.tags:
        legacy_disabled += 1
expected_active = sorted([actor.get_actor_label() for actor in fixtures] + [sun.get_actor_label(), sky.get_actor_label()])
if sorted(active_lights) != expected_active:
    fail("unexpected active-light set: " + repr(sorted(active_lights)))

roof_labels = [label for label in by_label if label.startswith("2126 ") and "roof" in label.lower()]
wheel_labels = [label for label in by_label if label.startswith("2126 ") and any(word in label.lower() for word in ("wheel", "tyre", "tire"))]
if roof_labels or wheel_labels:
    fail("roof or ordinary-wheel actors violate 2126 direction")

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    fail("read-only final audit changed protected authority")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__2126_FULLHALL_FINAL_STATE_CONTRACTS",
    "map": MAP,
    "actor_count_total": len(actors),
    "required_process_actor_count": len(REQUIRED),
    "separate_3d_coils": coil_rows,
    "process_fields": zone_rows,
    "native_collision_proxy_count": len(collision_labels),
    "native_collision_proxies": collision_labels,
    "detailed_hover_pallets": pallet_rows,
    "native_sequence": sequence.get_path_name(),
    "native_sequence_binding_count": len(bindings),
    "fixed_camera": {"pitch": rotation.pitch, "yaw": rotation.yaw, "projection": "ORTHOGRAPHIC"},
    "B_stylized": {"fixture_count": 6, "fixture_lumens": 1200.0, "fixture_kelvin": 5000.0, "sun": 0.30, "sky": 0.20, "exposure_bias": -0.50},
    "active_lights": sorted(active_lights),
    "disabled_legacy_light_count": legacy_disabled,
    "legacy_press_actor_count": 0,
    "ordinary_wheel_actor_count": 0,
    "roof_actor_count": 0,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FINAL_STATE_AUDIT_PASS output=" + str(OUT))
unreal.SystemLibrary.quit_editor()
