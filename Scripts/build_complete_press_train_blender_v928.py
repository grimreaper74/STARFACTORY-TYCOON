"""Build the corrected straight-through S01-S07 Blender assembly from approved assets."""
import bpy
from pathlib import Path
from mathutils import Matrix

transfer_blend = r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\SegmentedTransferRuntime_v746\Cairnwell_InterPressTransfer_Runtime_v746.blend"
out_dir = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\StraightThroughAssembly_v20260810_v928")
out_dir.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
station_x = {
    "S01_Destack_Load": -22.5,
    "S02_ApprovedWalkerStation": -15.0,
    "S03_ApprovedWalkerStation": -7.5,
    "S04_ApprovedWalkerStation": 0.0,
    "S05_ApprovedWalkerStation": 7.5,
    "S06_ApprovedWalkerStation": 15.0,
    "S07_Unload_Inspection_Robot": 22.5,
}

# Remove the incorrect interstage roller beds and the old review-only discharge roller.
for obj in list(scene.objects):
    if obj.name.startswith("InterStageRoller_") or obj.name == "S07_Discharge_Roller":
        bpy.data.objects.remove(obj, do_unlink=True)

# Preserve the approved module rotations/scales, changing only the verified stage centres.
for name, x in station_x.items():
    obj = scene.objects.get(name)
    if not obj:
        raise RuntimeError(f"Missing approved station instance {name}")
    obj.location.x = x

# Remove the obsolete 86 m review floor/arrows; a clean render floor is added at render time.
for obj in list(scene.objects):
    if obj.name.startswith("REVIEW_") or obj.type == "FONT" or "IdentityPlaque" in obj.name or "IdentityFrame" in obj.name:
        bpy.data.objects.remove(obj, do_unlink=True)

# Append the already approved four-part transfer traverse and reproduce it at the six
# interstage midpoints. Its authored internal offsets and materials remain untouched.
with bpy.data.libraries.load(transfer_blend, link=False) as (data_from, data_to):
    data_to.objects = list(data_from.objects)
source_objects = [o for o in data_to.objects if o and o.type == "MESH"]
if len(source_objects) != 4:
    raise RuntimeError(f"Expected four traverse objects, found {len(source_objects)}")

runtime = bpy.data.collections.new("CA_MW_StraightThroughPressTrain_v928")
scene.collection.children.link(runtime)
gap_centres = [-18.75, -11.25, -3.75, 3.75, 11.25, 18.75]
for gap_index, gap_x in enumerate(gap_centres, start=1):
    for source in source_objects:
        clone = source.copy()
        clone.data = source.data.copy()
        clone.name = f"TR{gap_index:02d}__{source.name}"
        runtime.objects.link(clone)
        # Raise the authored traverse so its vacuum cup plane sits on the 1.1 m blank line.
        clone.matrix_world = Matrix.Translation((gap_x, 0.0, 1.55)) @ source.matrix_world

scene["LB_STAGE_PITCH_M"] = 7.5
scene["LB_PANEL_FLOW_AXIS"] = "+X"
scene["LB_PANEL_TRANSFER_HEIGHT_M"] = 1.1
scene["LB_PLAYER_PLACEABLE_UNIT"] = True
scene["LB_ASSET_GATE"] = "S01_PLACEHOLDER_PENDING_PRO; S02-S06_APPROVED_WALKER; TRANSFER_APPROVED_V746; S07_APPROVED_V787"

out = out_dir / "Cairnwell_PressTrain_StraightThrough_PlayerUnit_v928.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(out), copy=True)
print("LINE_BOSS_STRAIGHT_THROUGH_TRAIN_BLEND_V928_PASS", out)
