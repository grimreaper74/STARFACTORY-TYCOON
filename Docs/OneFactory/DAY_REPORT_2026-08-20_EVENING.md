# Day report - 2026-08-20 (evening)

You asked this morning for three things before wishlist day: perfect
placements, higher-detail models everywhere, and UI improvements.
Here is where each stands tonight.

## 1. Every machine model is now high detail

The journey sweep you set ("start at press, from coils to finished
car") finished its authoring today. Since this morning:

- **Paint - all 33 meshes rebuilt** (batches 5-8): the PF track
  portals and carriers, the ED dip tank with its ribbed walls and
  service walk, the seven booth/tunnel shells (glazed spray booth,
  flash-off, vision light tunnel, pretreatment wash, ED hood, curing
  oven, tack-off), the robot service decks, PF drive and switch
  towers, turntable, body skid, and all the back-of-house plant
  (AHU, extraction, scrubber trench, dosing/mix/UF/sludge skids,
  burner house, oven stack, and the two robot spray tools).
- **Assembly - all 26 remaining meshes rebuilt** (batches 9-12):
  trim line (body lowerator, door climb and carriers, cockpit assist
  and module, nutrunner rail, andon board), chassis and marriage
  (heavy gantry, floor marriage table, hangers, scissor platform,
  urethane pump, fluid fill, glass rack), final line (wheel carousel
  and rack with real dished wheels, alignment bed, headlamp aim rig,
  fit gauge, sequenced carts), and EOL (water leak test booth, EOL
  arch, flash gantry, store bay).
- Weld's 26 and the intake set (AGVs, destack, cleaning dock,
  trailer, tractor) were finished earlier today. Press machines are
  Codex's authored trains - the reference standard - and stay.

Every rebuild is footprint-true, so the shop layouts you approved
did not move. Every batch was previewed in Blender before import and
defects fixed before anything entered the game (floating gussets,
merged drums, wheels piercing shelves - all caught at preview).

## 2. Placements are measured perfect, not eyeballed

The placement QA now sweeps all 3,679 placed machine actors for
interpenetration, floaters and sinkers. Tonight it reads:

    actors: 3,679 | overlaps: 0 | height issues: 0

Getting there surfaced one real corruption and several real clashes:

- A blanket mesh re-import had corrupted the weld robot's J2 joint
  with three stray vertices sitting nine kilometres off the model -
  every robot's bounds spanned the whole shop. Fixed at source, and
  the importer now takes a scoped include list so a repair can never
  blanket-refresh pieces owned by other pipelines again.
- Real re-pitches: the paint services row (bigger AHU and extraction
  bodies), signal pillars at the weld line heads, and the weld
  station ring - the underbody fixture is 6.2 x 4.8 m in a 6.4 m
  pitch, so its tip dresser, cabinet and HMI pedestal all had to
  leave its envelope.
- The QA also learned the plant's by-design relationships (robots
  composed at stations, carriers riding deck plates, boards hanging
  across the track, the transporter kingpin coupling, the dyno pit)
  so future runs only flag genuine mistakes.

A full five-stop tour capture (`uplift_verify_*` in
Saved/Screenshots/WindowsEditor) verified all shops at the
management camera: dense, coherent, nothing floating or clipped.

## 3. UI

UI v2 (the mockup-matched HUD) shipped last night. The v2.1 pass
landed four slices this afternoon, each suite-gated (288 green):

- **Production graphs**: clicking a shop card now shows a trailing
  rate sparkline in the detail panel, tinted with the group's status
  colour - "how has this line been doing" at a glance.
- **Alert memory**: the inbox gains a RECENT section; resolved
  alerts no longer vanish silently but stay listed with the sim
  clock they cleared at (D2 14:05).
- **Card tooltips**: hovering a flow card shows stations, live
  units, measured vs capacity rate and cycle progress in full.
- **Camera bookmarks**: Shift+F5-F8 saves a view, F5-F8 jumps back
  to it - the onboarding hint teaches it.

Still scoped for v2.1's next wave: order queue panel, bottleneck
highlighting, day summary and a settings/UI-scale surface.

## Build

Tonight's build is at `Packaged/Dev_2026-08-20_evening/Windows/
LineBossCarFactory.exe` - BuildCookRun succeeded and a boot smoke
loaded the Moorcross map clean (one production flow authority, one
runtime coordinator, exit 0). It carries everything above.

## Codex

His work-day queue (Steam capsule drafts, colourways, texture sets
for the staged FBXs, LODs, decal sheets) had not delivered by the
time of this report; whatever lands overnight gets audited and
integrated tomorrow, textures bound by slot name as usual.
