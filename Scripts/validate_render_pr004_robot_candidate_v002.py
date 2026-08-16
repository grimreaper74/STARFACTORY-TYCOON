"""Run the shared PR-004 robot FBX and render gate for candidate v002."""

from pathlib import Path
import os
import runpy


os.environ["LB_PR004_ROBOT_VERSION"] = "v002"
runpy.run_path(str(Path(__file__).with_name("validate_render_pr004_robot_candidate_v001.py")))
