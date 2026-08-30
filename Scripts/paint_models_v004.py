"""The hall interior comes off hand-mixed tints and onto the palette.

v003 painted these four by eye, before the brand spec existed. The
gantry crane got SAFETY yellow - linear (0.93, 0.72, 0.06), which is
sRGB #F8DE45 at saturation 72% and value 97%. Measured off the rendered
frame it lands at S 0.78 / V 0.70, over the machine-amber ceiling of
S 0.69 / V 0.66 on BOTH axes, on the largest machine in the hall.

That is not a near miss, it is the wrong ROLE. The spec assigns safety
yellow to "floor infrastructure only - never on machine bodies, robot
arms, crates, hulls, the UI", and it names what a gantry is under
Structure.Graphite: "columns, GANTRY LEGS, rails, roof trusses". A
crane is structure. It was painted like a floor marking.

Why it matters beyond looking wrong: the whole palette exists so the
ships are the most colourful thing on screen. A 20 m saturated yellow
portal straddling the line is the one object guaranteed to beat a
customer livery, and the spec's rule for that case is not negotiable -
LOWER THE MACHINERY, NEVER RAISE THE LIVERY.

The other three move onto palette tokens in the same pass rather than
being left as the last hand-mixed values in the hall.

Supersedes paint_models_v003.py; that file stays as evidence.
"""
import unreal

MASTER = "/Game/LineBoss/Materials/Surfaces/M_LB_Surface_Master"
PAINT_DIR = "/Game/LineBoss/Materials/Paint"
INTERIOR = "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

# THE PALETTE, in linear, matching LBSpacecraftPalette.h exactly. The
# authored sRGB hex is beside each one so a drift between this file and
# the header is visible rather than silent.
STRUCTURE_GRAPHITE = unreal.LinearColor(0.068, 0.074, 0.080, 1.0)  # #4A4D50
GRAPHITE_DARK = unreal.LinearColor(0.033, 0.037, 0.042, 1.0)       # #33363A
HOUSING_PALE = unreal.LinearColor(0.672, 0.644, 0.597, 1.0)        # #D6D2CB
MACHINE_AMBER = unreal.LinearColor(0.392, 0.171, 0.034, 1.0)       # #A87334
CRATE_TAN = unreal.LinearColor(0.451, 0.296, 0.138, 1.0)           # #B39468
CRATE_TAN_DARK = unreal.LinearColor(0.270, 0.171, 0.080, 1.0)      # #8E7350

TARGETS = [
    # THE FIX. Graphite THROUGHOUT, because a gantry is structure.
    #
    # The first attempt put machine amber on the accent channel and
    # measured S 0.60 / V 0.79 on the crossbeam - still over the
    # ceiling, because the panel mask spreads the accent across the
    # big girders rather than picking out details. The spec limits
    # amber to "arm segments, fitting heads and edge strips"; a 20 m
    # beam is none of those, so amber on it repeats the original
    # mistake at a lower saturation.
    #
    # The amber belongs on the HOIST, which is the part that actually
    # moves and is drawn separately in code.
    {"mesh": "SM_LB_IN_GantryCrane", "name": "GantryCrane",
     "tint": STRUCTURE_GRAPHITE, "accent": GRAPHITE_DARK, "rough": 0.52},

    # Crates are crates: the tan sits a deliberate 27 saturation points
    # below machine amber so a floor of parts and a floor of machines
    # do not merge into one orange field seen from above.
    {"mesh": "SM_LB_IN_StockpileRack", "name": "StockpileRack",
     "tint": CRATE_TAN, "accent": CRATE_TAN_DARK, "rough": 0.62},

    # Columns are structure too, but they are the BACKDROP the machines
    # stand against, so they take the pale housing rather than the
    # graphite - a hall of graphite columns reads as a cave.
    {"mesh": "SM_LB_IN_HallColumn", "name": "HallColumn",
     "tint": HOUSING_PALE, "accent": STRUCTURE_GRAPHITE, "rough": 0.60},

    {"mesh": "SM_LB_IN_DispatchDoor", "name": "DispatchDoor",
     "tint": HOUSING_PALE, "accent": GRAPHITE_DARK, "rough": 0.58},
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
        # A refusal, not a fallback. A mesh silently painted flat looks
        # like success in a receipt and like a bug on screen.
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
    for index in range(len(slots)):
        mesh.set_material(index, instance)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    painted.append("%s -> %s" % (target["mesh"], path))
    unreal.log("PAINT v004: %s repainted from the palette" % target["name"])

for line in painted:
    unreal.log("PAINT v004 OK  %s" % line)
for line in failures:
    unreal.log_error("PAINT v004 REFUSED  %s" % line)
unreal.log("PAINT v004: %d painted, %d refused"
           % (len(painted), len(failures)))
if failures:
    # Fails the run rather than reporting a partial success: half a
    # repaint leaves the hall in two palettes at once.
    raise SystemExit(1)
