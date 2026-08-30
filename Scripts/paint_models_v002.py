"""Paint the three GROUND CREW drones, which v001 left flat white.

CORRECTION, and it matters more than the paint. An earlier draft of
this docstring claimed the ground crew were the "white blocks at the
bottom of each station" the owner asked about on 2026-08-28. THAT WAS
WRONG, and it was written before any of it had been tested.

The white blocks are the PARTS STOCKPILE RACKS
(SM_LB_IN_StockpileRack) - see paint_models_v003.py. Proven by tagging:
tinting all three drone-side meshes changed nothing about them, and
tinting the rack turned every one magenta. The run log also contains
ZERO SM_LB_GD_* meshes, because LB.Spacecraft.BuildLine installs only
assembly drones; the ground crew appear in the real starting loadout,
not in that dev command.

The correction is left in rather than quietly deleted because the wrong
claim did real damage while it stood: a fleet of code-reading agents
was asked to identify the object independently, found THIS FILE, and
returned the wrong answer with high confidence, quoting this docstring
back as decisive evidence. An unverified assertion written into the
repo becomes someone else's ground truth. Do not write a conclusion
here until an experiment has produced it.

WHAT THIS LANE STILL DOES, on its own merits: the three ground drones
genuinely were flat white, and for a measurable reason: 

  * all three wear MI_LB_Surface_PalePanel, whose WearAmount is 0 and
    whose MaskStrength is 0, so the material resolves to ONE FLAT TINT
    across the whole mesh;
  * their folder (GroundDrones_v001) contains THREE meshes and ZERO
    textures, so unlike the flying drones there is no BaseColor map to
    use as a panel mask;
  * and the meshes are not featureless - 6472, 7018 and 9707 triangles
    respectively. The detail is there. A single unshaded tone was
    hiding all of it, wheels included.

So this is the HEIGHT route the master gained for exactly this case:
dark chassis and running gear below, pale body above, no texture
required.

HEIGHT CONTRAST IS COMPUTED PER MESH, NOT GUESSED. The master
normalises the vertical term by the object's BOUNDING SPHERE RADIUS,
which on a wide flat vehicle is dominated by its LENGTH. Measured, the
raw term only spans:

    GD_Lifter    320x202x84   0.39..0.61 of its 0..1 range
    GD_Assembly  300x201x171  0.29..0.71
    GD_Sprayer   320x205x212  0.26..0.74

A gradient living in the middle fifth of its range is invisible. Rather
than hardcode a gain that would silently become wrong the moment a mesh
is replaced, each instance derives its own from the mesh it is painting:

    gain = 0.9 * radius / halfHeight

which lands the top of the mesh at roughly 0.95 of the mask whatever
its proportions. A replacement mesh gets a correct value for free.

Reversible: each slot's previous material is recorded in the receipt.
Fail-closed: refuses a mesh it cannot measure rather than painting it
with a guessed constant.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/painted_models_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

MASTER = "/Game/LineBoss/Materials/Surfaces/M_LB_Surface_Master"
PAINT_DIR = "/Game/LineBoss/Materials/Painted"
GROUND = "/Game/LineBoss/Candidates/Spacecraft/GroundDrones_v001"

# BaseTint is the BOTTOM of the mesh and AccentTint the TOP - the mask
# runs 0 at the underside to 1 at the crown. Dark running gear under a
# pale body is how real plant is built and how both reference games
# read; the reverse would put the dark tone on the roof.
CHASSIS = unreal.LinearColor(0.24, 0.24, 0.26, 1.0)
BODY = unreal.LinearColor(0.82, 0.81, 0.78, 1.0)

TARGETS = [
    {"mesh": "%s/SM_LB_GD_Lifter" % GROUND, "name": "GroundLifter"},
    {"mesh": "%s/SM_LB_GD_Assembly" % GROUND, "name": "GroundAssembly"},
    {"mesh": "%s/SM_LB_GD_Sprayer" % GROUND, "name": "GroundSprayer"},
]

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("Refusing to paint: the surface master is missing.")
# The master must actually carry HeightContrast, or every instance below
# sets a parameter that does not exist and the grade silently stays
# flat - the same class of silent failure as the Nanite usage flags.
names = [str(p) for p in mel.get_scalar_parameter_names(master)]
if "HeightContrast" not in names:
    raise RuntimeError(
        "FAIL CLOSED: the surface master has no HeightContrast parameter. "
        "Run build_lineboss_surface_master_v006.py first, or every grade "
        "here would silently do nothing. Found: %s" % ", ".join(sorted(names)))

failures = []
painted = []

for target in TARGETS:
    mesh = library.load_asset(target["mesh"])
    if mesh is None:
        failures.append("mesh missing: %s" % target["mesh"])
        continue

    extent = mesh.get_bounds().box_extent
    radius = math.sqrt(extent.x ** 2 + extent.y ** 2 + extent.z ** 2)
    if extent.z <= 1.0 or radius <= 1.0:
        # Refuse rather than fall back to a constant: a wrong gain looks
        # like a working material and reads as "the grade does nothing".
        failures.append("cannot measure %s (halfZ=%.2f radius=%.2f), "
                        "refusing to guess a contrast"
                        % (target["name"], extent.z, radius))
        continue
    contrast = 0.9 * radius / extent.z

    path = "%s/MI_LB_Paint_%s" % (PAINT_DIR, target["name"])
    if library.does_asset_exist(path):
        instance = library.load_asset(path)
    else:
        instance = tools.create_asset(
            "MI_LB_Paint_%s" % target["name"], PAINT_DIR,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(instance, master)
    mel.set_material_instance_vector_parameter_value(
        instance, "BaseTint", CHASSIS)
    mel.set_material_instance_vector_parameter_value(
        instance, "AccentTint", BODY)
    # No texture exists for these, so the panel-mask path stays off and
    # the whole grade comes from height.
    mel.set_material_instance_scalar_parameter_value(
        instance, "MaskStrength", 0.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "HeightBlend", 1.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "HeightContrast", contrast)
    mel.set_material_instance_scalar_parameter_value(
        instance, "WearAmount", 0.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "Roughness", 0.50)
    mel.set_material_instance_scalar_parameter_value(
        instance, "Metallic", 0.05)
    # A little relief, so the panel lines the mesh does have catch light
    # instead of disappearing into the flat tone that hid them.
    mel.set_material_instance_scalar_parameter_value(
        instance, "NormalStrength", 0.30)
    library.save_loaded_asset(instance, only_if_is_dirty=False)

    slots = mesh.get_editor_property("static_materials")
    was = []
    for index in range(len(slots)):
        previous = slots[index].material_interface
        was.append(previous.get_path_name() if previous else None)
        mesh.set_material(index, instance)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

    reloaded = library.load_asset(target["mesh"])
    stuck = all(
        slot.material_interface is not None
        and slot.material_interface.get_path_name().startswith(path)
        for slot in reloaded.get_editor_property("static_materials"))
    if not stuck:
        failures.append("%s did not keep its painted material" % target["name"])
    painted.append({
        "mesh": target["mesh"], "instance": path,
        "size_cm": [round(extent.x * 2), round(extent.y * 2),
                    round(extent.z * 2)],
        "bounding_radius_cm": round(radius, 1),
        "height_contrast": round(contrast, 2),
        "raw_mask_span": [round(0.5 - (extent.z / radius) * 0.5, 2),
                          round(0.5 + (extent.z / radius) * 0.5, 2)],
        "slots": len(was), "was": was, "verified": stuck})

report = {
    "$schema": "lineboss/audit/painted-models-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__GROUND_CREW_PAINTED" if not failures
               else "PARTIAL__GROUND_CREW_PAINTED"),
    "why": ("The ground crew wore the flat PalePanel instance - one "
            "tint over 6-9k triangles of detail, wheels included. "
            "Their folder has no textures, so the height grade rather "
            "than a panel mask is the route. NOTE: these are NOT the "
            "'white blocks at the bottom of each station' the owner "
            "asked about - those are the stockpile racks, see "
            "painted_models_v003. That misidentification was written "
            "into this lane before it was tested."),
    "painted": painted,
    "failures": failures,
    "not_proven": [
        "NOBODY HAS LOOKED AT IT YET. The contrast is derived rather "
        "than guessed, but derived is not the same as judged - a "
        "capture is the check.",
        "These meshes came back from Meshy with four wheels when the "
        "owner asked for six or eight, and that is still unresolved. "
        "Painting them makes the wheels VISIBLE; it does not make them "
        "the right wheels.",
        "NOT SEEN IN ANY CAPTURE. LB.Spacecraft.BuildLine installs only "
        "assembly drones, so no ground-crew mesh is loaded in the dev "
        "runs used for screenshots. This paint is unverified on screen "
        "until a run uses the real starting loadout.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("GROUNDPAINT %s painted=%d failures=%d"
      % (report["status"], len(painted), len(failures)))
for entry in painted:
    print("GROUNDPAINT  %s contrast=%.2f span=%s"
          % (entry["instance"].split("/")[-1], entry["height_contrast"],
             entry["raw_mask_span"]))
for failure in failures:
    print("GROUNDFAIL %s" % failure)
