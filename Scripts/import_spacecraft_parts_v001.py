"""Import the twelve spacecraft components and the five parts carriers.

PROVENANCE
  source  spacecraft-components3.glb  sha256 f3e1148c... (geometry)
          parts-carriers4.glb         sha256 57ead25a... (geometry)
          Both commissioned through Claude Design, 2026-08-29, and
          delivered as one multi-object GLB each.
  route   text prompt -> generated geometry -> measured -> corrected.
          The components took two rounds (the canopy came back with
          Spitfire-style ribs over the glass) and the carriers three
          (a cable spool measured 78.7% silhouette overlap with the
          sealed crate at gameplay size, so it was replaced with an
          open cage pallet at 62.2%).
  colour  Assigned as FLAT PER-SLOT BASE COLOURS from the palette, with
          NO baked texture maps - verified zero embedded images in both
          drops. Every value landed within 1/255 of spec except
          dark_rubber at 5/255.

WHY EACH PART IS ITS OWN GLB
  Interchange does not honour combine requests. The components drop
  holds 230 sub-meshes under 12 named parts; imported as delivered that
  is 230 static meshes in the content browser rather than 12. They are
  pre-joined in Blender, which also preserves the material slots.

THE LIVERY SLOT
  Every component carries a slot named livery_accent on its bands,
  latches and edge strips. It ships NEUTRAL GREY on purpose. In game it
  is driven to the customer's colour, so a contract's ship gets matching
  accents on every fitted part without a second model. It arrived as
  saturated warning orange and was renamed and neutralised - baked
  colour there would have made every ship come out the same.
"""
import unreal

ROOT = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
        r"\SourceAssets\Spacecraft")
DEST_ROOT = "/Game/LineBoss/Candidates/Spacecraft"

# Measured after the Blender join - that is what actually imports.
# Checked BOTH WAYS: an import far UNDER budget means geometry was lost
# in translation, which reads as success if you only test the ceiling.
BUDGETS = {
    "Components_v001": {
        "LB_Part_antenna_dish": 7360,
        "LB_Part_avionics_rack": 552,
        "LB_Part_cargo_door": 7816,
        "LB_Part_cockpit_canopy": 5248,
        "LB_Part_crew_seat": 228,
        "LB_Part_docking_collar": 4752,
        "LB_Part_engine_nozzle": 30496,
        "LB_Part_landing_gear_leg": 3708,
        "LB_Part_propellant_tank": 10736,
        "LB_Part_radiator_panel": 676,
        "LB_Part_rcs_thruster_pod": 3460,
        "LB_Part_reaction_wheel": 2796,
    },
    "Drones_v001": {
        # Two rounds. The first had no lifting mechanism at all on a
        # machine whose entire job is lifting; the second gained deep
        # rotor ducts and sprung legs. A third round chasing "heavier"
        # was dropped after rendering it through the real game camera -
        # at 30 m it is 402 px wide and the thin fuselage that looked
        # wrong in a hero shot is invisible.
        #
        # 12,636 AFTER JOINING, not the 3,624 the GLB reports. Six
        # rotors and four legs are INSTANCES sharing one mesh each, so
        # the file's triangle total is a third of what actually imports.
        # Budgeting from the file would have set a guard the real mesh
        # trips immediately.
        "LB_Drone_cargo_drone": 12636,
        # The assembly drone: the machine the player watches most, since
        # it is the drones that fit parts rather than robot arms. Its
        # predecessor had three-fingered claws and a two-lens face on a
        # machine in a factory where nothing is hand-operated; this one
        # has parallel-jaw grippers and an instrument strip.
        "LB_Drone_assembly_drone": 7112,
    },
    "PaintBooth_v001": {
        # MANDATORY - CommissionFactory refuses to run a line without a
        # spray booth - and until now it had no model at all: 26 m of
        # engine cubes. It is also where the game's ONE colour decision
        # happens, since the factory stays neutral and each contract
        # paints the craft in its customer's livery, so the glazing is a
        # gameplay requirement rather than styling.
        #
        # 7.80 m tall EXACTLY, and that is coupled to the gantry: the
        # portal travels over this building at an 11.0 m bridge
        # underside. A taller booth would clip a crane that already
        # exists.
        "LB_Booth_paint_booth": 5028,
    },
    "LiftCradle_v001": {
        # FIVE SEPARATE OBJECTS ON PURPOSE. The game moves each stage
        # independently, so a merged lift would import cleanly, look
        # right in a still, and be frozen the moment the line ran.
        #
        # Modelled EXTENDED, because a mesh cannot reveal surfaces it
        # was authored without - the stages slide DOWN from this pose
        # to retract. It replaces the one block on a station that never
        # had a mesh: a 7.2 x 3.4 m untextured slab lying on the floor.
        "LB_Lift_lift_base": 240,
        "LB_Lift_lift_stage_1": 292,
        "LB_Lift_lift_stage_2": 88,
        "LB_Lift_lift_stage_3": 124,
        "LB_Lift_lift_saddle": 352,
    },
    "TrackSet_v002": {
        # Laying track is the player's primary build verb, so these are
        # looked at more than anything else in the game - and the meshes
        # they replace were a CONVEYOR BELT, an idiom dropped when the
        # gantry took over moving the craft.
        #
        # The 4.00 m module is the one number here that fails loudly: an
        # error of 2 cm becomes a 32 cm gap over sixteen pieces and reads
        # as a repeating seam rather than a single flaw. The turn came
        # back first as a 3.30 m curved wedge and had to be redone as a
        # square tile.
        "LB_Track_track_straight": 276,
        "LB_Track_track_turn": 880,
        "LB_Track_track_end_cap": 360,
    },
    "Gantry_v002": {
        # GENERATED, not commissioned. Three briefs for this machine
        # produced three plausible wrong ones - two monorails and a
        # portal rotated a quarter turn - because "gantry crane on a
        # rail" describes both machines and no adjective says which axis
        # the bridge crosses. A portal is defined by numbers the project
        # already holds, so Scripts/build_gantry_portal.py builds it
        # from GantryRailSpanCm() instead.
        #
        # FOUR PIECES BECAUSE THEY MOVE SEPARATELY: the rails are
        # static, the portal travels along them, the trolley traverses
        # the bridge and the hoist lowers. The Meshy drop fused crane
        # and rails into one object, which would slide the track down
        # the hall with the crane.
        "LB_Gantry_rails": 528,
        "LB_Gantry_portal": 408,
        "LB_Gantry_trolley": 264,
        "LB_Gantry_hoist": 312,
    },
    "Carriers_v001": {
        "LB_Carrier_bundled_stock": 984,
        "LB_Carrier_cage_pallet": 1004,
        "LB_Carrier_open_tray": 204,
        "LB_Carrier_pressure_canister": 6080,
        "LB_Carrier_sealed_crate": 180,
    },
}
TOLERANCE = 0.10


def fail(reason):
    unreal.log_error("SPACECRAFT PARTS IMPORT REFUSED: %s" % reason)
    raise SystemExit(1)


tools = unreal.AssetToolsHelpers.get_asset_tools()
registry = unreal.AssetRegistryHelpers.get_asset_registry()
problems = []

for folder, budget in BUDGETS.items():
    dest = "%s/%s" % (DEST_ROOT, folder)
    if unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.log("PARTS: clearing previous import at %s" % dest)
        unreal.EditorAssetLibrary.delete_directory(dest)

    for name in sorted(budget):
        path = "%s\%s\%s.glb" % (ROOT, folder, name)
        if not unreal.Paths.file_exists(path):
            fail("source missing: %s" % path)
        task = unreal.AssetImportTask()
        task.filename = path
        task.destination_path = dest
        task.automated = True
        task.replace_existing = True
        task.save = True
        tools.import_asset_tasks([task])

    meshes = {}
    for data in registry.get_assets_by_path(dest, recursive=True):
        asset = data.get_asset()
        if isinstance(asset, unreal.StaticMesh):
            meshes[asset.get_name()] = asset

    for name, declared in sorted(budget.items()):
        mesh = next((m for k, m in meshes.items() if k.startswith(name)), None)
        if mesh is None:
            problems.append("%s: NOT IMPORTED" % name)
            continue
        nanite = mesh.get_editor_property("nanite_settings").enabled
        # get_num_triangles(0) reports the FALLBACK mesh under Nanite, so
        # a Nanite import legitimately reads far below its declared count
        # and must not be judged against it.
        actual = mesh.get_num_triangles(0)
        b = mesh.get_bounds().box_extent
        slots = [str(s.material_slot_name) for s in mesh.static_materials]
        unreal.log(
            "PARTS %-32s %7d tris (fallback)  %5.2f x %5.2f x %5.2f m  "
            "nanite=%s  slots=%s"
            % (name, actual, b.x * 2 / 100.0, b.y * 2 / 100.0,
               b.z * 2 / 100.0, nanite, ",".join(slots)))
        if not nanite:
            if actual > declared * (1.0 + TOLERANCE):
                problems.append("%s: %d tris OVER declared %d"
                                % (name, actual, declared))
            elif actual < declared * (1.0 - TOLERANCE):
                problems.append("%s: %d tris UNDER declared %d - geometry "
                                "lost on import" % (name, actual, declared))
        if "livery_accent" in slots:
            unreal.log("PARTS   %s carries the livery slot" % name)

    unreal.log("PARTS: %d meshes under %s" % (len(meshes), dest))

if problems:
    for p in problems:
        unreal.log_error("PARTS PROBLEM: %s" % p)
    fail("%d budget or import problems" % len(problems))

# COUNTED, not asserted. This line read "all 17 masters" while
# nineteen were importing - a hardcoded total drifts the moment a
# model is added, and a wrong count in a passing log is worse than
# no count at all.
unreal.log("PARTS: all %d masters imported within budget"
           % sum(len(b) for b in BUDGETS.values()))
