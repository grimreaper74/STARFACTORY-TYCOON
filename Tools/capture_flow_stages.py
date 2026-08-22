"""Capture the six production-flow card images from the live map.

Replaces the Meshy-derived authority renders: one clean in-editor
capture per flow stage, framed on the placed machinery.
"""
import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/FlowStages/"

# (name, camera x, y, z, yaw, pitch)
SHOTS = (
    ("01_CoilIntake", -24200.0, 8200.0, 1500.0, 215.0, -18.0),
    ("02_BlankBuffer", -22500.0, 3500.0, 1400.0, 195.0, -16.0),
    ("03_TransferPress", -20500.0, -1200.0, 1600.0, 205.0, -14.0),
    ("04_PanelStillages", -17800.0, -6800.0, 1500.0, 160.0, -16.0),
    ("05_BodyWeld", -12000.0, -8400.0, 1600.0, 155.0, -15.0),
    ("06_EDCoat", 9000.0, -5000.0, 1500.0, 200.0, -14.0),
)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

tasks = []
for name, x, y, z, yaw, pitch in SHOTS:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(x, y, z), unreal.Rotator(pitch, yaw, 0.0))
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1600, 900, OUT + name + ".png")
    tasks.append((name, task))
    unreal.log("QUEUED " + name)

# Tick the editor until every screenshot task reports done.
import time
frame_budget = 2000


def all_done():
    return all(t.is_task_done() for _, t in tasks)


ticks = 0
while not all_done() and ticks < frame_budget:
    unreal.SystemLibrary.delay
    time.sleep(0.05)
    ticks += 1
unreal.log("FLOW_CAPTURE done={} ticks={}".format(all_done(), ticks))
