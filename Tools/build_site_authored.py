"""Author the Moorcross Works site into the level with real assets.

The site used to be generated at runtime from scaled engine cubes. The owner
asked for it to be built in the editor instead, so this places real meshes as
saved actors: the vendor chainlink fence and gate leaves, a Blender-native
four-coil artic at the dock bays, shipping containers in the marshalling area,
the vendor hangar and box buildings as support blocks, and the background towers
as a skyline beyond the fence. Ground, roads and paint use tinted instances of
the project's own world-aligned procedural concrete master, so a yard hundreds of
metres across tiles correctly instead of stretching a texture.

Every dimension derives from the AUTHORED department bays in
Source/LineBossCarFactory/LBOneFactoryTypes.cpp, the same source the shop
envelopes size themselves from, so the site cannot drift out of register with
the buildings.

Run headless. It MUST be -ExecutePythonScript: under -run=pythonscript there is
no editor world, so load_level and every spawn silently return nothing and the
script still exits 0.
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/build_site_authored.py
"""
import io
import json
import os

import unreal

LEVEL = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
SITE_TAG = "LB.Site.Authored"
MATERIAL_DIR = "/Game/LineBoss/Site/Materials_v001"
OUT = os.environ.get("LB_SITE_OUT", "C:/Temp/lb_site.json")

CONCRETE_MASTER = ("/Game/LineBoss/Materials/Environment/"
                   "M_LB_SealedFactoryConcrete_World_v001")
PAINT_MASTER = ("/Game/LineBoss/Materials/FrontEnd/"
                "M_LB_FrontEndPaintedConcrete_Master")

MESH = {
    "plane": "/Engine/BasicShapes/Plane",
    "fence": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Fence_01",
    "post": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_FencePart_01",
    "gate_leaf": "/Game/Meshes/SM_GateDoor01",
    "gate_border": "/Game/Meshes/SM_GateBorder01",
    "container_a": "/Game/Meshes/SM_Container01_01",
    "container_b": "/Game/Meshes/SM_Container01_02",
    "container_tall": "/Game/Meshes/SM_ContainerP4_01",
    "hangar": "/Game/Meshes/SM_Background2_Hangar",
    "box_building": "/Game/Meshes/SM_Background2_BoxBuilding",
    "box_base": "/Game/Meshes/SM_Background2_BoxBuildingBase",
    "pillar": "/Game/Meshes/SM_ConcretePillar01",
    "wall": "/Game/Meshes/SM_ConcreteWall",
    "spotlight": "/Game/Meshes/SM_CrashAreaSpotlight_01",
    # NOT SM_CA_MW_InboundLorry_Approved_v006. Its only material is
    # M_CA_MW_Lorry_MeshyPBR_v006, and ActorUsesForbiddenProvenance rejects any
    # actor binding a 'Meshy' path. Nine of those placed as saved level actors
    # made the bootstrap reject the world and locked the factory out of
    # commissioning entirely, while the test suite still reported 278/278. This
    # assembly is Blender-native and clean; verified by
    # Tools/Diagnostics/probe_lorry_provenance.py.
    "lorry": ("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/"
              "LorryAssemblyCandidate_v005/SM_CA_MW_Inbound_LorryFourCoil_v005"),
    "tower01": "/Game/Meshes/SM_Background1_Tower01",
    "tower02": "/Game/Meshes/SM_Background1_Tower02",
    "tower03": "/Game/Meshes/SM_Background1_Tower03",
    "tower04": "/Game/Meshes/SM_Background1_Tower04",
    "antenna": "/Game/Meshes/SM_Background1_AntennaTower",
}

# Measured bounding sizes in cm, from Tools/Diagnostics/probe_site_assets.py.
FENCE_PANEL_CM = 128.2
FENCE_HEIGHT_CM = 100.8

REPORT = {"placed": {}, "cleared": 0, "notes": []}


# --------------------------------------------------------------------------
# The authored department bays. Mirrors MakeMoorcrossWorksShellLayout() in
# Source/LineBossCarFactory/LBOneFactoryTypes.cpp; keep the two in step.
# --------------------------------------------------------------------------
BAYS = {
    "Press":    ((-14500.0, 8000.0), (32000.0, 13000.0)),
    "Body":     ((-11000.0, -8500.0), (18000.0, 10000.0)),
    "Paint":    ((10000.0, -8500.0), (22000.0, 10000.0)),
    "Assembly": ((16500.0, 8500.0), (28000.0, 12000.0)),
}
SHOP_SKIRT_CM = 400.0


class Rect(object):
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x, self.min_y = min_x, min_y
        self.max_x, self.max_y = max_x, max_y

    @property
    def width(self):
        return self.max_x - self.min_x

    @property
    def depth(self):
        return self.max_y - self.min_y

    @property
    def cx(self):
        return (self.min_x + self.max_x) * 0.5

    @property
    def cy(self):
        return (self.min_y + self.max_y) * 0.5

    def expanded(self, west, east, south, north):
        return Rect(self.min_x - west, self.min_y - south,
                    self.max_x + east, self.max_y + north)


def bay_rect(name):
    (cx, cy), (sx, sy) = BAYS[name]
    return Rect(cx - sx * 0.5 - SHOP_SKIRT_CM, cy - sy * 0.5 - SHOP_SKIRT_CM,
                cx + sx * 0.5 + SHOP_SKIRT_CM, cy + sy * 0.5 + SHOP_SKIRT_CM)


PRESS = bay_rect("Press")
BODY = bay_rect("Body")
PAINT = bay_rect("Paint")
ASSEMBLY = bay_rect("Assembly")
SHOPS = Rect(min(r.min_x for r in (PRESS, BODY, PAINT, ASSEMBLY)),
             min(r.min_y for r in (PRESS, BODY, PAINT, ASSEMBLY)),
             max(r.max_x for r in (PRESS, BODY, PAINT, ASSEMBLY)),
             max(r.max_y for r in (PRESS, BODY, PAINT, ASSEMBLY)))

# The shops stand in two rows; the spine yard is the open band between them,
# which the production route already crosses.
SPINE_Y = (max(BODY.max_y, PAINT.max_y) + min(PRESS.min_y, ASSEMBLY.min_y)) * 0.5

APRON = SHOPS.expanded(12000.0, 11000.0, 15000.0, 13000.0)
RING = APRON.expanded(4200.0, 4200.0, 4200.0, 4200.0)
FENCE = RING.expanded(3800.0, 3800.0, 3800.0, 3800.0)

# Ground heights. The shop envelope lays its own slab from -11 to -1, so site
# surfacing sits below that and roads and paint just above it.
Z_GRASS = -30.0
Z_ASPHALT = -18.0
Z_CONCRETE = -16.0
Z_ROAD = 3.0
Z_PAINT = 5.0

GATE_Y = SHOPS.min_y - 11000.0


# --------------------------------------------------------------------------
# Editor helpers
# --------------------------------------------------------------------------
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

LOADED = {}


def mesh(key):
    if key not in LOADED:
        asset = unreal.load_asset(MESH[key])
        if asset is None:
            raise RuntimeError("missing mesh for '{}': {}".format(key, MESH[key]))
        LOADED[key] = asset
    return LOADED[key]


def make_material(name, parent_path, vectors=None, scalars=None):
    """Create (or refresh) a tinted instance of one of the project's masters."""
    package = "{}/{}".format(MATERIAL_DIR, name)
    existing = unreal.load_asset(package)
    if existing is None:
        parent = unreal.load_asset(parent_path)
        if parent is None:
            raise RuntimeError("missing material master {}".format(parent_path))
        existing = ASSET_TOOLS.create_asset(
            name, MATERIAL_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        unreal.MaterialEditingLibrary.set_material_instance_parent(
            existing, parent)
    for parameter, value in (vectors or {}).items():
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            existing, parameter, value)
    for parameter, value in (scalars or {}).items():
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            existing, parameter, value)
    unreal.EditorAssetLibrary.save_loaded_asset(existing, False)
    # Read the tints back. The grass and asphalt instances looked identical to
    # plain concrete in the first lit capture, and a silently-ignored parameter
    # name would look exactly the same as an over-exposed one - so record what
    # actually stuck rather than assuming the set calls took.
    readback = {}
    for parameter in (vectors or {}):
        try:
            colour = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(
                existing, parameter)
            readback[parameter] = [round(colour.r, 4), round(colour.g, 4),
                                   round(colour.b, 4)]
        except Exception:  # noqa: BLE001 - report rather than fail the build
            readback[parameter] = "unreadable"
    REPORT.setdefault("material_readback", {})[name] = readback
    return existing


def count(kind, amount=1):
    REPORT["placed"][kind] = REPORT["placed"].get(kind, 0) + amount


def place(kind, mesh_key, location, rotation=(0.0, 0.0, 0.0), scale=None,
          material=None, label=None):
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh(mesh_key), unreal.Vector(*location), unreal.Rotator(*rotation))
    if actor is None:
        REPORT["notes"].append("failed to spawn {} at {}".format(mesh_key, location))
        return None
    if scale is not None:
        actor.set_actor_scale3d(unreal.Vector(*scale))
    if material is not None:
        component = actor.static_mesh_component
        for slot in range(component.get_num_materials()):
            component.set_material(slot, material)
    actor.tags = [unreal.Name(SITE_TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    if label:
        actor.set_actor_label(label)
    count(kind)
    return actor


def horizontal_extent(mesh_key):
    """The mesh's longest horizontal side, and the yaw that aims it along +X.

    Measured from the asset so swapping a vehicle for another of a different
    length or build axis does not need any pitch or offset retuning.
    """
    box = mesh(mesh_key).get_bounding_box()
    size = box.max - box.min
    if size.x >= size.y:
        return size.x, 0.0
    return size.y, 90.0


def slab(kind, rect, top_z, material, label=None):
    """A ground surface. The concrete master is world-aligned, so a plane can
    be scaled to any size without the texture stretching."""
    return place(kind, "plane", (rect.cx, rect.cy, top_z),
                 scale=(rect.width / 100.0, rect.depth / 100.0, 1.0),
                 material=material, label=label)


def stripe(rect, top_z, material, label=None):
    return slab("paint", rect, top_z, material, label)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
if not LEVEL_SUB.load_level(LEVEL):
    raise RuntimeError("could not load {}".format(LEVEL))

# Fail loudly if the wrong world is open. Run under -run=pythonscript this
# script placed nothing and still reported success: a commandlet has no editor
# world, so every spawn silently returned None. Check the world's identity
# rather than its actor count - the Moorcross map is deliberately a near-empty
# shell, because the factory itself is spawned at runtime by the bootstrap.
WORLD = unreal.EditorLevelLibrary.get_editor_world()
if WORLD is None or LEVEL.rsplit("/", 1)[-1] != WORLD.get_name():
    raise RuntimeError(
        "expected world '{}' but the editor has '{}'. Run with "
        "-ExecutePythonScript, not -run=pythonscript.".format(
            LEVEL.rsplit("/", 1)[-1],
            "<none>" if WORLD is None else WORLD.get_name()))
EXISTING_ACTORS = ACTOR_SUB.get_all_level_actors()
REPORT["notes"].append(
    "level loaded with {} pre-existing actor(s)".format(len(EXISTING_ACTORS)))

# Clear anything this script placed on a previous run, so it is idempotent and
# never doubles up the site.
for actor in EXISTING_ACTORS:
    if actor and unreal.Name(SITE_TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

MAT_ASPHALT = make_material(
    "MI_LB_Site_Asphalt_v001", CONCRETE_MASTER,
    vectors={"ConcreteTint": unreal.LinearColor(0.048, 0.050, 0.054, 1.0),
             "JointTint": unreal.LinearColor(0.070, 0.072, 0.076, 1.0)},
    scalars={"SlabSizeCm": 1400.0, "Roughness": 0.86,
             "MacroVariationStrength": 0.35, "FineVariationStrength": 0.25,
             "JointHalfWidthRatio": 0.004})
MAT_CONCRETE = make_material(
    "MI_LB_Site_Concrete_v001", CONCRETE_MASTER,
    vectors={"ConcreteTint": unreal.LinearColor(0.290, 0.295, 0.280, 1.0),
             "JointTint": unreal.LinearColor(0.200, 0.205, 0.195, 1.0)},
    scalars={"SlabSizeCm": 600.0, "Roughness": 0.80,
             "MacroVariationStrength": 0.30, "FineVariationStrength": 0.30})
# Undeveloped ground. This was first tinted green as a grass stand-in, but a
# concrete master cannot be made to read as grass: with the tint verifiably set
# to green it still rendered grey-brown, because the tint modulates a concrete
# base rather than replacing it. Tinting it toward dry hardcore instead is
# honest - undeveloped land on an industrial site genuinely is levelled gravel,
# not lawn - and it stops the site pretending to have planting it does not have.
# Real grass and trees need a vegetation pack; see the note appended below.
MAT_GRASS = make_material(
    "MI_LB_Site_LevelledHardcore_v001", CONCRETE_MASTER,
    vectors={"ConcreteTint": unreal.LinearColor(0.042, 0.036, 0.026, 1.0),
             "JointTint": unreal.LinearColor(0.036, 0.031, 0.022, 1.0)},
    scalars={"SlabSizeCm": 4000.0, "Roughness": 0.95,
             "MacroVariationStrength": 0.85, "FineVariationStrength": 0.55,
             "JointHalfWidthRatio": 0.0})
MAT_WHITE = make_material(
    "MI_LB_Site_PaintWhite_v001", PAINT_MASTER,
    vectors={"ZoneTint": unreal.LinearColor(0.900, 0.895, 0.860, 1.0)},
    scalars={"TintStrength": 1.0})
MAT_YELLOW = make_material(
    "MI_LB_Site_PaintYellow_v001", PAINT_MASTER,
    vectors={"ZoneTint": unreal.LinearColor(0.900, 0.700, 0.020, 1.0)},
    scalars={"TintStrength": 1.0})
REPORT["notes"].append(
    "undeveloped ground uses MI_LB_Site_LevelledHardcore_v001, a tinted concrete "
    "instance reading as levelled gravel: the project contains no vegetation mesh "
    "or grass material, so planting needs a Fab vegetation pack (Quixel "
    "Megaplants and the Megascans tree sets are free) added to Content/")

# ---- ground ---------------------------------------------------------------
# The ground has to run out to the horizon, not stop just beyond the fence.
# At 12 m of margin the site read as a floating slab in the sky and the skyline
# towers stood in void, so the field extends far past the works and the fog
# takes over before its edge.
slab("ground", FENCE.expanded(150000.0, 150000.0, 150000.0, 150000.0), Z_GRASS,
     MAT_GRASS, "Site_Grass_Field")
slab("ground", APRON, Z_ASPHALT, MAT_ASPHALT, "Site_Yard_Hardstanding")

# ---- roads ----------------------------------------------------------------
RING_WIDTH = 1400.0
SERVICE_WIDTH = 1200.0


def road(from_x, from_y, to_x, to_y, width, label):
    along_x = abs(to_x - from_x) >= abs(to_y - from_y)
    length = abs(to_x - from_x) if along_x else abs(to_y - from_y)
    if length < 1.0:
        return
    cx, cy = (from_x + to_x) * 0.5, (from_y + to_y) * 0.5
    surface = (Rect(cx - length * 0.5, cy - width * 0.5,
                    cx + length * 0.5, cy + width * 0.5) if along_x
               else Rect(cx - width * 0.5, cy - length * 0.5,
                         cx + width * 0.5, cy + length * 0.5))
    slab("road", surface, Z_ROAD, MAT_ASPHALT, label)

    # Solid edge lines, then a dashed centre line.
    for side in (-1.0, 1.0):
        offset = side * (width * 0.5 - 70.0)
        edge = (Rect(cx - length * 0.5, cy + offset - 7.0,
                     cx + length * 0.5, cy + offset + 7.0) if along_x
                else Rect(cx + offset - 7.0, cy - length * 0.5,
                          cx + offset + 7.0, cy + length * 0.5))
        stripe(edge, Z_PAINT, MAT_WHITE, label + "_Edge")
    dash_pitch = 640.0
    dashes = max(1, int(length // dash_pitch))
    start = (cx if along_x else cy) - length * 0.5
    for index in range(dashes):
        at = start + dash_pitch * (index + 0.5)
        dash = (Rect(at - 160.0, cy - 7.0, at + 160.0, cy + 7.0) if along_x
                else Rect(cx - 7.0, at - 160.0, cx + 7.0, at + 160.0))
        stripe(dash, Z_PAINT, MAT_WHITE, label + "_Dash")


road(RING.min_x, RING.min_y, RING.max_x, RING.min_y, RING_WIDTH, "Road_Ring_S")
road(RING.min_x, RING.max_y, RING.max_x, RING.max_y, RING_WIDTH, "Road_Ring_N")
road(RING.min_x, RING.min_y, RING.min_x, RING.max_y, RING_WIDTH, "Road_Ring_W")
road(RING.max_x, RING.min_y, RING.max_x, RING.max_y, RING_WIDTH, "Road_Ring_E")
road(RING.min_x, SPINE_Y, RING.max_x, SPINE_Y, SERVICE_WIDTH, "Road_Spine")
NORTH_SERVICE_Y = SHOPS.max_y + 5200.0
SOUTH_SERVICE_Y = SHOPS.min_y - 5200.0
road(RING.min_x, NORTH_SERVICE_Y, RING.max_x, NORTH_SERVICE_Y, SERVICE_WIDTH,
     "Road_Service_N")
road(RING.min_x, SOUTH_SERVICE_Y, RING.max_x, SOUTH_SERVICE_Y, SERVICE_WIDTH,
     "Road_Service_S")
# No road through the middle of the works: the alley between the press and
# assembly bays is two metres wide by authorship, so the north-south yard roads
# run in the open yards beyond the end walls.
road(SHOPS.min_x - 6200.0, RING.min_y, SHOPS.min_x - 6200.0, RING.max_y,
     SERVICE_WIDTH, "Road_Yard_W")
road(SHOPS.max_x + 5600.0, RING.min_y, SHOPS.max_x + 5600.0, RING.max_y,
     SERVICE_WIDTH, "Road_Yard_E")
road(FENCE.min_x - 11000.0, GATE_Y, RING.min_x, GATE_Y, RING_WIDTH,
     "Road_Gate_Approach")

# ---- perimeter fence, in runs of real chainlink panels ---------------------
def fence_run(from_x, from_y, to_x, to_y, gap_centre=None, gap_half=0.0):
    along_x = abs(to_x - from_x) >= abs(to_y - from_y)
    length = abs(to_x - from_x) if along_x else abs(to_y - from_y)
    panels = max(1, int(round(length / FENCE_PANEL_CM)))
    pitch = length / panels
    base = min(from_x, to_x) if along_x else min(from_y, to_y)
    fixed = from_y if along_x else from_x
    for index in range(panels):
        at = base + pitch * (index + 0.5)
        if gap_centre is not None and abs(at - gap_centre) < gap_half:
            continue
        location = (at, fixed, 0.0) if along_x else (fixed, at, 0.0)
        place("fence", "fence", location,
              rotation=(0.0, 0.0 if along_x else 90.0, 0.0),
              scale=(pitch / FENCE_PANEL_CM, 1.0, 1.0))
    # A post every eighth panel reads as a straining post without doubling the
    # actor count.
    for index in range(0, panels, 8):
        at = base + pitch * index
        if gap_centre is not None and abs(at - gap_centre) < gap_half:
            continue
        location = (at, fixed, 0.0) if along_x else (fixed, at, 0.0)
        place("fence_post", "post", location, scale=(1.0, 1.0, 1.05))


fence_run(FENCE.min_x, FENCE.min_y, FENCE.max_x, FENCE.min_y)
fence_run(FENCE.min_x, FENCE.max_y, FENCE.max_x, FENCE.max_y)
fence_run(FENCE.max_x, FENCE.min_y, FENCE.max_x, FENCE.max_y)
fence_run(FENCE.min_x, FENCE.min_y, FENCE.min_x, FENCE.max_y,
          gap_centre=GATE_Y, gap_half=RING_WIDTH * 0.5 + 300.0)

# ---- gatehouse -----------------------------------------------------------
for side, sign in (("N", 1.0), ("S", -1.0)):
    place("gate", "gate_border",
          (FENCE.min_x, GATE_Y + sign * (RING_WIDTH * 0.5 + 200.0), 0.0),
          label="Gate_Border_" + side)
    for leaf in range(3):
        place("gate", "gate_leaf",
              (FENCE.min_x,
               GATE_Y + sign * (RING_WIDTH * 0.5 + 200.0 - 125.0 * (leaf + 1)),
               0.0),
              rotation=(0.0, 90.0, 0.0), label="Gate_Leaf_{}{}".format(side, leaf))
# Gatehouse itself: a box building on its base, with a barrier each side.
place("gatehouse", "box_base", (FENCE.min_x + 2600.0, GATE_Y - 2400.0, 0.0),
      scale=(0.75, 0.75, 1.0), label="Gatehouse_Base")
place("gatehouse", "box_building", (FENCE.min_x + 2600.0, GATE_Y - 2400.0, 200.0),
      scale=(0.55, 0.55, 0.42), label="Gatehouse")
for lane, sign in ((0, 1.0), (1, -1.0)):
    place("gatehouse", "pillar",
          (FENCE.min_x + 1500.0, GATE_Y + sign * 320.0, 0.0),
          scale=(0.22, 0.22, 0.32), label="Gate_Barrier_{}".format(lane))

# ---- lorry docks: press west wall, assembly east wall --------------------
def dock_row(shop, west_wall, bays, label):
    wall_x = shop.min_x if west_wall else shop.max_x
    sign = -1.0 if west_wall else 1.0
    apron = (Rect(wall_x - 9000.0, shop.min_y, wall_x, shop.max_y) if west_wall
             else Rect(wall_x, shop.min_y, wall_x + 9000.0, shop.max_y))
    slab("apron", apron, Z_CONCRETE, MAT_CONCRETE, label + "_Apron")
    usable = shop.depth - 2000.0
    pitch = usable / max(1, bays)
    for index in range(bays):
        bay_y = shop.min_y + 1000.0 + pitch * (index + 0.5)
        # Hazard hatching at the dock face.
        stripe(Rect(wall_x + sign * 520.0 if west_wall else wall_x,
                    bay_y - (pitch * 0.5 - 60.0),
                    wall_x if west_wall else wall_x + 520.0,
                    bay_y + (pitch * 0.5 - 60.0)),
               Z_PAINT, MAT_YELLOW, label + "_Hatch")
        # Reversing guide lines out into the apron.
        for side in (-1.0, 1.0):
            side_y = bay_y + side * (pitch * 0.5 - 60.0)
            stripe(Rect(wall_x + sign * 5200.0 if west_wall else wall_x,
                        side_y - 7.0,
                        wall_x if west_wall else wall_x + 5200.0,
                        side_y + 7.0),
                   Z_PAINT, MAT_WHITE, label + "_Guide")
        if index % 2 == 0:
            length, base_yaw = horizontal_extent("lorry")
            place("lorry", "lorry",
                  (wall_x + sign * (length * 0.5 + 150.0), bay_y, 0.0),
                  rotation=(0.0, base_yaw + (0.0 if west_wall else 180.0), 0.0),
                  label="{}_Artic_{}".format(label, index))


dock_row(PRESS, True, 10, "Dock_Inbound_Press")
dock_row(ASSEMBLY, False, 8, "Dock_Dispatch_Assembly")

# ---- stillage marshalling: real containers -------------------------------
for row in range(3):
    for column in range(9):
        key = ("container_a", "container_b", "container_tall")[(row + column) % 3]
        if (row * 9 + column) % 7 == 5:
            continue
        place("container", key,
              (SHOPS.min_x - 8200.0 + row * 3400.0,
               SPINE_Y - 5200.0 - column * 640.0, 0.0),
              label="Stillage_Container_{}_{}".format(row, column))

# ---- support blocks along the north service road -------------------------
BLOCK_Y = SHOPS.max_y + 9600.0
# The vendor hangar is 62.8 x 145.4 m, so it is rotated to run east-west and
# scaled down to the depth the north band allows.
place("block", "hangar", (-24000.0, BLOCK_Y, 0.0), rotation=(0.0, 90.0, 0.0),
      scale=(0.42, 1.05, 0.62), label="Block_DieWarehouse")
place("block", "hangar", (2000.0, BLOCK_Y, 0.0), rotation=(0.0, 90.0, 0.0),
      scale=(0.40, 0.78, 0.55), label="Block_MaintenanceWorkshop")
for index in range(3):
    place("block", "box_base", (14000.0 + index * 2100.0, BLOCK_Y, 0.0),
          label="Block_Utilities_Base_{}".format(index))
    place("block", "box_building", (14000.0 + index * 2100.0, BLOCK_Y, 200.0),
          scale=(1.0, 1.0, 0.7), label="Block_Utilities_{}".format(index))
place("block", "box_base", (26000.0, BLOCK_Y, 0.0), scale=(1.1, 0.9, 1.0),
      label="Block_ControlRoom_Base")
place("block", "box_building", (26000.0, BLOCK_Y, 200.0), scale=(1.15, 0.95, 1.4),
      label="Block_ControlRoom")
slab("apron", Rect(SHOPS.min_x, BLOCK_Y - 8000.0, SHOPS.max_x, BLOCK_Y - 2600.0),
     Z_CONCRETE, MAT_CONCRETE, "Block_Standing")

# ---- serviced plots kept clear for shops not yet built -------------------
# Line Boss is build-your-own, so the site must show where the works can grow:
# levelled, kerbed and with services already run to the plot edge.
for index, plot in enumerate((
        Rect(-22000.0, SHOPS.min_y - 16000.0, -2000.0, SHOPS.min_y - 7000.0),
        Rect(6000.0, SHOPS.min_y - 16000.0, 26000.0, SHOPS.min_y - 7000.0))):
    slab("plot", plot, Z_GRASS + 14.0, MAT_GRASS,
         "Future_Plot_{}".format("AB"[index]))
    # Kerb the plot with the vendor concrete wall so it reads as allocated
    # ground rather than spare field.
    for along_x, fixed_lo, fixed_hi in ((True, plot.min_y, plot.max_y),
                                        (False, plot.min_x, plot.max_x)):
        span = plot.width if along_x else plot.depth
        stones = max(1, int(round(span / 402.5)))
        pitch = span / stones
        base = plot.min_x if along_x else plot.min_y
        for fixed in (fixed_lo, fixed_hi):
            for stone in range(stones):
                at = base + pitch * (stone + 0.5)
                place("plot_kerb", "wall",
                      (at, fixed, 0.0) if along_x else (fixed, at, 0.0),
                      rotation=(0.0, 0.0 if along_x else 90.0, 0.0),
                      scale=(pitch / 402.5, 1.0, 0.14))
    place("plot", "pillar", (plot.cx - 400.0, plot.max_y + 900.0, 0.0),
          scale=(0.30, 0.30, 0.26),
          label="Future_Plot_{}_ServiceStub".format("AB"[index]))

# ---- staff car park ------------------------------------------------------
CAR_PARK = Rect(SHOPS.min_x - 10800.0, SHOPS.min_y - 15200.0,
                SHOPS.min_x - 800.0, SHOPS.min_y - 7200.0)
slab("apron", CAR_PARK, Z_ASPHALT + 1.0, MAT_ASPHALT, "StaffCarPark")
SPACE_CM = 250.0
SPACE_DEPTH_CM = 500.0
ROW_PITCH = SPACE_DEPTH_CM * 2.0 + 600.0
rows = int(CAR_PARK.depth // ROW_PITCH)
spaces = int((CAR_PARK.width - 600.0) // SPACE_CM)
for row in range(rows):
    row_min_y = CAR_PARK.min_y + 300.0 + row * ROW_PITCH
    for rank in range(2):
        rank_y = row_min_y + rank * SPACE_DEPTH_CM
        for space in range(spaces + 1):
            space_x = CAR_PARK.min_x + 300.0 + space * SPACE_CM
            stripe(Rect(space_x - 6.0, rank_y, space_x + 6.0,
                        rank_y + SPACE_DEPTH_CM), Z_PAINT, MAT_WHITE,
                   "CarPark_Bay")
        stripe(Rect(CAR_PARK.min_x + 300.0,
                    rank_y + (0.0 if rank == 0 else SPACE_DEPTH_CM) - 6.0,
                    CAR_PARK.min_x + 300.0 + spaces * SPACE_CM,
                    rank_y + (0.0 if rank == 0 else SPACE_DEPTH_CM) + 6.0),
               Z_PAINT, MAT_WHITE, "CarPark_Head")
REPORT["placed"]["car_park_spaces"] = rows * 2 * spaces

# ---- yard lighting -------------------------------------------------------
for index in range(14):
    fraction = (index + 0.5) / 14.0
    place("light_mast", "spotlight",
          (RING.min_x + RING.width * fraction, RING.max_y + 900.0, 1100.0),
          rotation=(0.0, 180.0, 0.0), scale=(1.4, 1.4, 1.4))
    place("light_mast", "spotlight",
          (RING.min_x + RING.width * fraction, RING.min_y - 900.0, 1100.0),
          scale=(1.4, 1.4, 1.4))

# ---- skyline beyond the fence -------------------------------------------
# Real background meshes so the horizon is not empty sky. All outside the
# fence line, so nothing here is mistaken for part of the works.
SKYLINE = [
    ("tower03", (-64000.0, 52000.0), (1.0, 1.0, 1.0)),
    ("tower04", (-38000.0, 58000.0), (1.0, 1.0, 0.9)),
    ("tower01", (-12000.0, 54000.0), (1.0, 1.0, 1.1)),
    ("antenna", (16000.0, 60000.0), (1.0, 1.0, 1.0)),
    ("tower02", (46000.0, 55000.0), (1.0, 1.0, 1.0)),
    ("tower03", (72000.0, 30000.0), (0.9, 0.9, 0.8)),
    ("tower04", (76000.0, -18000.0), (1.0, 1.0, 1.0)),
    ("tower01", (68000.0, -48000.0), (1.0, 1.0, 0.95)),
    ("tower02", (10000.0, -62000.0), (1.0, 1.0, 0.9)),
    ("tower03", (-42000.0, -66000.0), (0.95, 0.95, 0.85)),
    ("antenna", (-72000.0, -34000.0), (1.0, 1.0, 1.0)),
    ("tower01", (-78000.0, 8000.0), (1.0, 1.0, 1.05)),
]
for key, (x, y), scale in SKYLINE:
    place("skyline", key, (x, y, 0.0), scale=scale)

# --------------------------------------------------------------------------
# Refuse to save a world the bootstrap would reject. ActorUsesForbiddenProvenance
# fails any actor whose name, tags, mesh path or bound material path contains
# 'Meshy' or 'ExternalGenerated', and a single violation locks the factory out of
# commissioning. The 278-test suite does NOT cover this, so check it here: the
# first version of this script placed nine lorries binding a Meshy material and
# left the game unable to build a factory while the suite stayed green.
FORBIDDEN_TOKENS = ("meshy", "externalgenerated")
violations = []
for actor in ACTOR_SUB.get_all_level_actors():
    if not actor or unreal.Name(SITE_TAG) not in actor.tags:
        continue
    suspects = [actor.get_name(), actor.get_actor_label()]
    suspects.extend(str(tag) for tag in actor.tags)
    component = actor.static_mesh_component
    if component:
        asset = component.static_mesh
        if asset:
            suspects.append(asset.get_path_name())
        for slot in range(component.get_num_materials()):
            bound = component.get_material(slot)
            if bound:
                suspects.append(bound.get_path_name())
    for suspect in suspects:
        lowered = suspect.lower()
        for token in FORBIDDEN_TOKENS:
            if token in lowered:
                violations.append("{} -> {}".format(actor.get_actor_label(), suspect))
if violations:
    raise RuntimeError(
        "refusing to save: {} placed actor(s) trip the OneFactory provenance "
        "rule and would lock the factory out of commissioning. First: {}".format(
            len(violations), violations[0]))
REPORT["provenance_checked"] = True

LEVEL_SUB.save_current_level()

REPORT["geometry"] = {
    "shops": [SHOPS.min_x, SHOPS.min_y, SHOPS.max_x, SHOPS.max_y],
    "apron": [APRON.min_x, APRON.min_y, APRON.max_x, APRON.max_y],
    "ring": [RING.min_x, RING.min_y, RING.max_x, RING.max_y],
    "fence": [FENCE.min_x, FENCE.min_y, FENCE.max_x, FENCE.max_y],
    "site_size_m": [round(FENCE.width / 100.0, 1), round(FENCE.depth / 100.0, 1)],
    "spine_y": SPINE_Y,
}
REPORT["total"] = sum(v for k, v in REPORT["placed"].items()
                      if k != "car_park_spaces")
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE placed {} actors, cleared {}, site {}x{} m -> {}".format(
    REPORT["total"], REPORT["cleared"], REPORT["geometry"]["site_size_m"][0],
    REPORT["geometry"]["site_size_m"][1], OUT))
