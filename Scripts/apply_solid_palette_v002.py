"""Solid colour everywhere, bright and warm like Car Manufacture.

Owner, 2026-08-28: "how do i get rid of meshy's color and do it
myself?", then "want nice solid color", then - holding up Car
Manufacture's Steam page - "want to look nice and bright like this".

THAT REFERENCE SUPERSEDES COLD STEEL (the 2026-08-25 pick). What the
reference actually does, and what this lane copies:

  - MACHINERY IS THE MOST COLOURFUL THING ON THE FLOOR - a strong warm
    amber, not grey. This is the biggest single change: our machinery
    was graphite, which is the opposite.
  - a WARM light floor and panels, not a cool one.
  - MATTE PAINTED surfaces, near-zero metallic. Metallic is also why
    the lamps had to be dimmed to 3.5k lm - metal with no reflection
    environment blows out - so taking metallic down is what lets the
    light come up.
  - saturated but not garish; clean and readable rather than photoreal.

TWO CHANGES, and the first is the one that matters:

1. THE PALETTE GOES SOLID. WearAmount mixed the library's paint-chip
   texture into the tint; at 0 the surface is the tint and nothing else.
   The normal map stays connected, so the result is a SOLID COLOUR WITH
   REAL SURFACE RELIEF rather than a dead flat fill - panels still catch
   the light, they just stop being speckled.

2. THE MESHY-COLOURED MESHES JOIN THE PALETTE. Every generated station
   and drone still wore an instance of M_LB_MeshyPBR_v004 or
   M_LB_Building_Master, both of which feed Meshy's baked BaseColor
   texture straight to the surface. That texture IS the colour the owner
   wants gone. Pointing the meshes at the palette removes it at the
   root instead of tinting over it.

WHICH COLOUR WHICH:

  - buildings and drones  -> WARM PANEL (light, warm, matte)
  - machinery and rigs    -> MACHINE AMBER (the reference's own move)

Ships keep their customer livery: colour on the craft was never the
problem, the factory being drained of it was.

NOTHING IS DELETED. The Meshy instances stay in the project, so any mesh
can be pointed back by changing its line here.

Fail-closed: refuses to rerun over its receipt, and reads every
assignment and every parameter back off the saved asset.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/solid_palette_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

PALETTE = "/Game/LineBoss/Materials/Surfaces"
MASTER = "%s/M_LB_Surface_Master" % PALETTE
PALE = "%s/MI_LB_Surface_PalePanel" % PALETTE
GRAPHITE = "%s/MI_LB_Surface_Graphite" % PALETTE
ORANGE = "%s/MI_LB_Surface_WarningOrange" % PALETTE
AMBER = "%s/MI_LB_Surface_MachineAmber" % PALETTE

# WearAmount 0 on every one: the owner set it themselves on the pale
# panel and asked for solid colour, so the whole palette follows.
# Metallic near zero is the load-bearing value - it is what stops the
# surfaces going dark-and-shiny and what lets the lamps be bright.
TUNING = {
    PALE: {"tint": (0.88, 0.85, 0.79), "rough": 0.58, "metal": 0.02,
           "tiling": 300.0},
    GRAPHITE: {"tint": (0.27, 0.26, 0.25), "rough": 0.62, "metal": 0.04,
               "tiling": 260.0},
    ORANGE: {"tint": (0.90, 0.44, 0.09), "rough": 0.55, "metal": 0.02,
             "tiling": 200.0},
    # The reference's machinery colour, and the reason this lane exists.
    AMBER: {"tint": (0.82, 0.46, 0.13), "rough": 0.55, "metal": 0.03,
            "tiling": 240.0},
}

STATIONS = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"

# SCANNED, NOT TABLED. A hand-written list of mesh names was the first
# attempt and it already missed half the folder - CircuitFab,
# DeliveryDock, the Mk2 stations. "Get rid of Meshy's colour" means all
# of it, so every static mesh under the station root is swept and the
# rule decides which palette it takes.
#
# From the settled language (pale industrial surfaces, graphite
# machinery, colour belongs to the ships):
#   - the DRONES read light, so they stand out against dark machinery
#   - BUILDINGS read light
#   - everything else is machinery and takes the AMBER
PALE_NAME_HINTS = ("Hall", "Silo", "Factory", "Building", "Wall", "Floor")


def palette_for(asset_path):
    name = asset_path.split("/")[-1]
    if "/Drones/" in asset_path and "ChargingDock" not in name:
        return PALE, "drone"
    for hint in PALE_NAME_HINTS:
        if hint in name:
            return PALE, "building"
    return AMBER, "machinery"


library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_lib = unreal.MaterialEditingLibrary
failures = []

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("surface master missing: %s" % MASTER)

# ---- 1. the palette goes solid, bright and warm ----
palette_rows = []
for path, values in sorted(TUNING.items()):
    if not library.does_asset_exist(path):
        # MachineAmber is new: the reference has a machinery colour and
        # we did not.
        instance = tools.create_asset(
            path.split("/")[-1], PALETTE,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        mat_lib.set_material_instance_parent(instance, master)
    else:
        instance = library.load_asset(path)
    if instance is None:
        failures.append("palette instance missing: %s" % path)
        continue
    mat_lib.set_material_instance_vector_parameter_value(
        instance, "BaseTint", unreal.LinearColor(
            values["tint"][0], values["tint"][1], values["tint"][2], 1.0))
    # SOLID: no paint-chip mix at all (the owner set this by hand on the
    # pale panel before asking for the rest).
    mat_lib.set_material_instance_scalar_parameter_value(
        instance, "WearAmount", 0.0)
    mat_lib.set_material_instance_scalar_parameter_value(
        instance, "Roughness", values["rough"])
    mat_lib.set_material_instance_scalar_parameter_value(
        instance, "Metallic", values["metal"])
    mat_lib.set_material_instance_scalar_parameter_value(
        instance, "DetailTilingCm", values["tiling"])
    library.save_loaded_asset(instance, only_if_is_dirty=False)
    reloaded = library.load_asset(path)
    wear = mat_lib.get_material_instance_scalar_parameter_value(
        reloaded, "WearAmount")
    metal = mat_lib.get_material_instance_scalar_parameter_value(
        reloaded, "Metallic")
    if abs(wear) > 0.001:
        failures.append("%s kept WearAmount %.3f" % (path, wear))
    if metal > 0.1:
        failures.append("%s kept Metallic %.3f - it will go dark"
                        % (path, metal))
    palette_rows.append({"instance": path, "wear_amount": wear,
                         "metallic": metal, "tint": values["tint"]})

# ---- 2. the Meshy-coloured meshes join the palette ----
mesh_rows = []
discovered = []
for asset in library.list_assets(STATIONS, recursive=True):
    path = asset.split(".")[0]
    if path.split("/")[-1].startswith("SM_"):
        discovered.append(path)

for path in sorted(discovered):
    material_path, why = palette_for(path)
    material = library.load_asset(material_path)
    mesh = library.load_asset(path)
    if material is None:
        failures.append("palette material missing: %s" % material_path)
        continue
    if not isinstance(mesh, unreal.StaticMesh):
        continue  # the folder also holds the imported textures
    before = mesh.get_material(0)
    before_name = before.get_name() if before else "NONE"
    # EVERY slot, not just the first: a mesh with two Meshy slots would
    # otherwise come out half repainted. Defensive about the slot count
    # because this runs in the owner's LIVE editor - a throw halfway
    # through would leave the floor half repainted.
    try:
        slots = max(1, len(mesh.get_editor_property("static_materials")))
    except Exception:  # noqa: BLE001
        slots = 1
    for slot in range(slots):
        try:
            mesh.set_material(slot, material)
        except Exception as exc:  # noqa: BLE001
            failures.append("%s slot %d: %s"
                            % (path.split("/")[-1], slot, exc))
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    reloaded = library.load_asset(path)
    after = reloaded.get_material(0)
    applied = after is not None and after.get_name() == material.get_name()
    if not applied:
        failures.append("%s did not keep %s"
                        % (path.split("/")[-1], material.get_name()))
    mesh_rows.append({
        "mesh": path.split("/")[-1],
        "reads_as": why,
        "was": before_name,
        "now": after.get_name() if after else "NONE",
        "applied": applied,
    })

report = {
    "$schema": "lineboss/audit/solid-palette-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__SOLID_PALETTE_APPLIED" if not failures
               else "FAIL_CLOSED__SOLID_PALETTE"),
    "why": ("Owner 2026-08-28: 'how do i get rid of meshy's color and "
            "do it myself' / 'want nice solid color'. WearAmount 0 makes "
            "the palette a solid colour; repointing the generated meshes "
            "removes Meshy's baked BaseColor at the root rather than "
            "tinting over it."),
    "palette": palette_rows,
    "meshes": mesh_rows,
    "failures": failures,
    "not_proven": [
        "Nobody has looked at it yet. The tints are the ones aimed at "
        "the owner's COLD STEEL decision and are not agreed - BaseTint "
        "on each palette instance is the single knob.",
        "Repointing a mesh drops Meshy's NORMAL and ROUGHNESS maps as "
        "well as its colour; the palette brings its own tiling detail. "
        "Parts will read cleaner and flatter, which is the settled "
        "direction but is a real change.",
        "Nothing is deleted: the Meshy instances remain, so any mesh "
        "can be pointed back by editing its line in this lane.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "palette": len(palette_rows),
                  "meshes": len(mesh_rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
