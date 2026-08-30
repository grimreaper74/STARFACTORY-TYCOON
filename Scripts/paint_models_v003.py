"""Paint the HALL INTERIOR - the third category I had been missing.

Owner, 2026-08-28, looking at a capture of the line:
"what's the white blocks at the bottom of each station ?"

They are the PARTS STOCKPILE RACKS - SM_LB_IN_StockpileRack, one placed
on the west flank of every line station, holding the parts that station
fits. Proven by tagging: every white block turned magenta when that one
mesh was tinted, having stayed white when all three drone-side meshes
were tagged first.

WHY THEY WERE WHITE, and why I had not noticed. The hall interior is
built by a Place() lambda in the presenter that sets a mesh, collision,
shadow and transform - and NEVER TOUCHES MATERIALS. So every interior
piece renders with whatever its mesh asset carries, which for all four
is the flat MI_LB_Surface_PalePanel: one unshaded tint over the whole
model. I had been thinking of the factory floor as stations plus
drones, and paint_models_v001 and v002 targeted exactly those two
categories. The hall furniture is a third one, and nothing had ever
pointed at it.

All four interior meshes ship base_color, normal and
metallic_roughness maps that have gone unused since import, so every
one of them can take the panel mask - luminance only, never the map's
colour, per the standing rule.

  StockpileRack  the parts waiting beside each station. Warm crate tone
                 with a dark frame, so it reads as loaded stock rather
                 than as a blank cabinet, and stays distinct from the
                 amber machinery it stands next to.
  GantryCrane    currently a dark scribble over the middle of the line.
                 Real gantry cranes are high-visibility; this makes it
                 safety yellow on a dark frame, which is both correct
                 and a large piece of colour the hall badly needs.
  HallColumn     structure, so pale panel over a dark base - the same
                 language as the walls.
  DispatchDoor   pale door leaf in a graphite frame.

Reversible: every slot's previous material is recorded. Fail-closed:
refuses a mesh whose mask texture is missing rather than painting it
flat and reporting success.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/painted_models_v003.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v004.")

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

MASTER = "/Game/LineBoss/Materials/Surfaces/M_LB_Surface_Master"
PAINT_DIR = "/Game/LineBoss/Materials/Painted"
INTERIOR = "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001"

CRATE = unreal.LinearColor(0.78, 0.55, 0.24, 1.0)
SAFETY = unreal.LinearColor(0.93, 0.72, 0.06, 1.0)
PALE = unreal.LinearColor(0.78, 0.77, 0.74, 1.0)
GRAPHITE = unreal.LinearColor(0.20, 0.20, 0.22, 1.0)
DARKFRAME = unreal.LinearColor(0.16, 0.16, 0.18, 1.0)

TARGETS = [
    {"mesh": "SM_LB_IN_StockpileRack", "name": "StockpileRack",
     "tint": CRATE, "accent": DARKFRAME, "rough": 0.62},
    {"mesh": "SM_LB_IN_GantryCrane", "name": "GantryCrane",
     "tint": SAFETY, "accent": DARKFRAME, "rough": 0.52},
    {"mesh": "SM_LB_IN_HallColumn", "name": "HallColumn",
     "tint": PALE, "accent": GRAPHITE, "rough": 0.60},
    {"mesh": "SM_LB_IN_DispatchDoor", "name": "DispatchDoor",
     "tint": PALE, "accent": GRAPHITE, "rough": 0.58},
]

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("Refusing to paint: the surface master is missing.")

failures = []
painted = []

for target in TARGETS:
    mesh_path = "%s/%s" % (INTERIOR, target["mesh"])
    mask_path = "%s/Textures/T_%s_base_color" % (INTERIOR, target["mesh"])
    mesh = library.load_asset(mesh_path)
    mask = library.load_asset(mask_path)
    if mesh is None:
        failures.append("mesh missing: %s" % mesh_path)
        continue
    if mask is None:
        # A refusal, not a fallback: a mesh silently painted flat looks
        # like success in a receipt and like a bug on screen - which is
        # exactly the state these four were already in.
        failures.append("mask missing, refusing to paint %s flat: %s"
                        % (target["name"], mask_path))
        continue

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
        instance, "BaseTint", target["tint"])
    mel.set_material_instance_vector_parameter_value(
        instance, "AccentTint", target["accent"])
    mel.set_material_instance_texture_parameter_value(
        instance, "PanelMask", mask)
    mel.set_material_instance_scalar_parameter_value(
        instance, "MaskStrength", 1.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "MaskPivot", 0.42)
    mel.set_material_instance_scalar_parameter_value(
        instance, "MaskContrast", 3.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "HeightBlend", 0.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "WearAmount", 0.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "Roughness", target["rough"])
    mel.set_material_instance_scalar_parameter_value(
        instance, "Metallic", 0.05)
    mel.set_material_instance_scalar_parameter_value(
        instance, "NormalStrength", 0.28)
    library.save_loaded_asset(instance, only_if_is_dirty=False)

    slots = mesh.get_editor_property("static_materials")
    was = []
    for index in range(len(slots)):
        previous = slots[index].material_interface
        was.append(previous.get_path_name() if previous else None)
        mesh.set_material(index, instance)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

    reloaded = library.load_asset(mesh_path)
    stuck = all(
        slot.material_interface is not None
        and slot.material_interface.get_path_name().startswith(path)
        for slot in reloaded.get_editor_property("static_materials"))
    if not stuck:
        failures.append("%s did not keep its painted material" % target["name"])
    painted.append({"mesh": mesh_path, "instance": path, "mask": mask_path,
                    "slots": len(was), "was": was, "verified": stuck})

# Clean up the identification tags - they were a diagnostic, and a
# stray emissive magenta instance in the project is a trap for later.
for tag in ("MI_LB_TagMagenta", "MI_LB_TagCyan", "MI_LB_TagGreen"):
    tag_path = "%s/%s" % (PAINT_DIR, tag)
    if library.does_asset_exist(tag_path):
        library.delete_asset(tag_path)

report = {
    "$schema": "lineboss/audit/painted-models-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__HALL_INTERIOR_PAINTED" if not failures
               else "PARTIAL__HALL_INTERIOR_PAINTED"),
    "why": ("The owner asked what the white blocks at the bottom of "
            "each station were. They are the parts stockpile racks, "
            "proven by tagging one mesh magenta and watching every "
            "white block change. They were white because the hall "
            "interior is placed by a lambda that never assigns a "
            "material, so all four interior meshes wore the flat "
            "PalePanel instance over unused base_color, normal and "
            "metallic_roughness maps."),
    "painted": painted,
    "failures": failures,
    "not_proven": [
        "NOBODY HAS LOOKED AT IT YET. A capture is the check.",
        "The tints are a first estimate in the settled language "
        "(machinery amber, structure pale, hazard yellow), not values "
        "the owner has picked.",
        "The presenter still assigns no material to hall interior "
        "pieces at all - this paints the ASSETS, so a future interior "
        "mesh added to that lambda will arrive flat white in exactly "
        "the same way unless it is painted too.",
        "The per-mesh normal and metallic_roughness maps remain unused; "
        "only base_color is consumed, and only as a mask.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("HALLPAINT %s painted=%d failures=%d"
      % (report["status"], len(painted), len(failures)))
for failure in failures:
    print("HALLFAIL %s" % failure)
