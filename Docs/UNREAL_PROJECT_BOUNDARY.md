# Line Boss Unreal project boundary

This is the clean Unreal 5.8 build of **Line Boss: Car Factory**. It lives at
`C:\Users\greg_\Projects\LineBossCarFactory_Unreal` and must never be moved to
OneDrive.

The Godot repository at `C:\Users\greg_\Projects\car factoy mayhem` remains
untouched and is the reference for simulation behaviour, station dimensions,
FreeCAD sources, Blender sources, process contracts and previous visual work.

## Import policy

- Do not copy the rejected exploded PR-005 Unreal parity scene into this project.
- Re-export custom machinery from authoritative `.blend` files one module at a
  time, preserving named moving assemblies and testing the HMI cabinet first.
- Use acquired packs only for environment modules, lights, fences, electrical
  props, generic platforms and background equipment.
- Never replace the Line Boss HMI, PR-004 crane, coils or hero process machines
  with generic vendor assets.
- Record every migrated vendor package and its licence/source under `Docs/`.

## First milestone

The initial map proves the exact 220 m x 120 m Press Shop footprint, 18 m clear
height, management camera framing, zone layout and PC renderer configuration.
It is a foundation map, not a claim that PR-005 or the Press Shop is complete.
