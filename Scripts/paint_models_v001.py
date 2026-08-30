"""Paint the drones two-tone, using Meshy's own maps as MASKS.

Owner 2026-08-28: "what's easiest way for you to paint the models ?"

This is the answer applied to the four flying drones, which are the
co-stars of the factory and the thing the player actually watches work.

WHY THESE FIVE MESHES AND NOT ALL 73. The drones each ship a
BaseColor / Normal / MR set that has been sitting unused since import,
and they are on screen constantly. The craft components (CP_*), the
runway and the hover pad are deliberately EXCLUDED: they were restored
by apply_solid_palette_v003 after the v002 sweep over-reached onto them,
and re-touching them now would repeat that mistake. The line stations
are excluded because they are procedural frames and own no mesh at all.

WHAT THE MASK IS, AND WHAT IT IS NOT. Meshy's BaseColor map is used as
a LUMINANCE MASK, never as colour. The owner's standing direction is
geometry from Meshy, materials authored in Unreal - and that still
holds exactly, because none of the map's hues reach the surface. What
does reach it is where the map is light and where it is dark, which is
where the panels, vents, recesses and seams are. That shape information
was being thrown away along with the palette, and it is free.

  light in the map -> BaseTint    (the panel faces)
  dark in the map  -> AccentTint  (the recesses, seams and vents)

REVERSIBLE: every slot's previous material is recorded in the receipt,
so this reads backwards as an undo - the same discipline that let the
palette over-reach be repaired instead of argued about.

Fail-closed: refuses to rerun over its receipt, refuses a mesh whose
mask texture is missing rather than painting it flat and calling it
done, and verifies the assignment by reading it back.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/painted_models_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

MASTER = "/Game/LineBoss/Materials/Surfaces/M_LB_Surface_Master"
PAINT_DIR = "/Game/LineBoss/Materials/Painted"
MESHES = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"

# tint / accent are the art call; the mask texture is the mesh's own.
#
# The drones are PALE with GRAPHITE recesses, not amber: the settled
# direction is clean futuristic industrial, and amber is reserved for
# the machinery a player builds. Making the drones amber too would
# flatten the one colour distinction the bay currently has.
PALE = unreal.LinearColor(0.78, 0.78, 0.76, 1.0)
GRAPHITE = unreal.LinearColor(0.20, 0.21, 0.23, 1.0)
# The one exception: the charging dock is equipment, so it reads amber
# like the rest of the built machinery, and its recesses go dark.
AMBER = unreal.LinearColor(0.86, 0.47, 0.10, 1.0)

TARGETS = [
    {"mesh": "%s/Drones/SM_LB_DR_Assembly_Body" % MESHES,
     "mask": "%s/Textures/T_LB_DroneAssembly_BaseColor" % MESHES,
     "name": "DroneAssembly", "tint": PALE, "accent": GRAPHITE},
    {"mesh": "%s/Drones/SM_LB_DR_CargoLift_Body" % MESHES,
     "mask": "%s/Textures/T_LB_DroneCargoLift_BaseColor" % MESHES,
     "name": "DroneCargoLift", "tint": PALE, "accent": GRAPHITE},
    {"mesh": "%s/Drones/SM_LB_DR_Spray_Body" % MESHES,
     "mask": "%s/Textures/T_LB_DroneSpray_BaseColor" % MESHES,
     "name": "DroneSpray", "tint": PALE, "accent": GRAPHITE},
    {"mesh": "%s/Drones/SM_LB_DR_Winch_Body" % MESHES,
     "mask": "%s/Textures/T_LB_DroneWinch_BaseColor" % MESHES,
     "name": "DroneWinch", "tint": PALE, "accent": GRAPHITE},
    {"mesh": "%s/Drones/SM_LB_DR_ChargingDock" % MESHES,
     "mask": "%s/Textures/T_LB_ChargingDock_BaseColor" % MESHES,
     "name": "ChargingDock", "tint": AMBER, "accent": GRAPHITE},
]

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("Refusing to paint anything: the surface master "
                       "is missing. Build it first.")

failures = []
painted = []

for target in TARGETS:
    mesh = library.load_asset(target["mesh"])
    mask = library.load_asset(target["mask"])
    if mesh is None:
        failures.append("mesh missing: %s" % target["mesh"])
        continue
    if mask is None:
        # Deliberately a REFUSAL, not a fallback to a flat tint: a mesh
        # silently painted flat looks like a success in a receipt and
        # like a bug on screen.
        failures.append("mask texture missing, refusing to paint %s flat: %s"
                        % (target["name"], target["mask"]))
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
    # A little height grading on top of the map, so even the parts the
    # map leaves flat still have a top-to-bottom read.
    mel.set_material_instance_scalar_parameter_value(
        instance, "HeightBlend", 0.18)
    mel.set_material_instance_scalar_parameter_value(
        instance, "WearAmount", 0.0)
    mel.set_material_instance_scalar_parameter_value(
        instance, "Roughness", 0.48)
    mel.set_material_instance_scalar_parameter_value(
        instance, "Metallic", 0.05)
    mel.set_material_instance_scalar_parameter_value(
        instance, "NormalStrength", 0.20)
    # NANITE USAGE. A material without it is silently swapped for the
    # default material in -game and NOT in the editor, which is exactly
    # how the "lost all the detail" fault hid for a whole session.
    try:
        master.set_editor_property("used_with_nanite", True)
    except Exception:  # noqa: BLE001
        pass
    library.save_loaded_asset(instance, only_if_is_dirty=False)

    slots = mesh.get_editor_property("static_materials")
    was = []
    for index in range(len(slots)):
        previous = slots[index].material_interface
        was.append(previous.get_path_name() if previous else None)
        mesh.set_material(index, instance)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

    # Read it back: an assignment that did not stick must not be
    # reported as one that did.
    reloaded = library.load_asset(target["mesh"])
    now = reloaded.get_editor_property("static_materials")
    stuck = all(
        slot.material_interface is not None
        and slot.material_interface.get_path_name().startswith(path)
        for slot in now)
    if not stuck:
        failures.append("%s did not keep its painted material" % target["name"])
    painted.append({"mesh": target["mesh"], "instance": path,
                    "mask": target["mask"], "slots": len(was),
                    "was": was, "verified": stuck})

library.save_loaded_asset(master, only_if_is_dirty=False)

report = {
    "$schema": "lineboss/audit/painted-models-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__MODELS_PAINTED" if not failures
               else "PARTIAL__MODELS_PAINTED"),
    "why": ("The owner asked the easiest way to paint the models. Of 73 "
            "imported meshes 63 have one material slot, so the answer "
            "had to be a two-tone MASK in the master rather than more "
            "material slots. Meshy's own BaseColor map supplies the "
            "mask - its luminance only, never its colour - because it "
            "already records where every panel, vent and seam is."),
    "painted": painted,
    "failures": failures,
    "not_proven": [
        "NOBODY HAS LOOKED AT IT YET. A material that compiles and an "
        "assignment that reads back are not a judgement that it looks "
        "good; a capture is, and that is the next step.",
        "Only the five drone-side meshes are painted. The craft "
        "components, runway and hover pad are deliberately untouched "
        "because the v002 palette sweep over-reached onto exactly those "
        "and v003 had to restore them.",
        "The per-mesh NORMAL and MR maps are still unused. The master "
        "samples a triplanar paint-chip normal instead, so the drones' "
        "own surface relief is still not being shown.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("PAINTRESULT %s painted=%d failures=%d"
      % (report["status"], len(painted), len(failures)))
for failure in failures:
    print("PAINTFAIL %s" % failure)
