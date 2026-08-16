"""Prove audio-only v027 inherits retained v024 physical policy exactly."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_audio_physical_inheritance_v026.py"
code = source.read_text(encoding="utf-8").replace("v026", "v027").replace("V026", "V027")
exec(compile(code, str(source) + "::v027", "exec"), globals(), globals())
