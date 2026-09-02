# The look plan, run through: phases A to F (2026-09-02, v001)

The owner approved `Docs/LOOK_JUDGEMENT_AND_PLAN_v001.md` at midday, said
"start on A", and on leaving for work: "can you finish all 6 phases
please" and "use meshy api if you need anything making that you cant do
yourself". This is the record of that afternoon: what each phase did, what
the frames show, what the tests cover, and what is not proven. Every claim
below points at a file.

## Where it started

Two frames at 11:30 (`Saved/Audits/LineLook_2026_09_02/judgement_*.png`):
pale on pale, four fifths bare floor, the craft a thumbnail, no station
silhouette, no colour, exposure four stops over.

## Phase A - contrast and warmth

- Cause found under "no value contrast": the map locks exposure at EV100
  0.0 while the lit scene averages 4.45. The player camera now locks
  exposure at the scene's level (linear multiplier 21; this project does
  not use the extended luminance range, so the first attempt at "4.2"
  read back as EV 2.1). `phaseA_hdr_readout_before.png` / `_after.png`.
- The interior floor never changed tone because the site's outdoor paving
  tiles stand proud of the hall's slab; the hall now lifts the 468 tiles
  under its footprint and its own floor shows.
- Floor a step lighter than the first "void" reading, a 10 m lane grid of
  16 cm lines, pale traffic lanes, mild warm sun, contact shadows.
- Frames: `phaseA_entry_lane_grid.png`, `phaseA_station1_lane_grid.png`.
- Commits d9ea1af, 1302bf1.

## Phase B - colour where the palette allows it

- The primer coat verified in a strong livery: a Coastal Rescue craft in
  muted pink from the first station (`phaseB_primer_coat_pink_livery_station5.png`).
- Amber and blue carried by the tool tower (cap, arm, strip) and the racks
  in Crate.Tan; the interface stays hue-free.
- Commit 892e7b2.

## Phase C - station presence

- Blockout first: one tool tower per station on the FAR flank. The first
  blockout put one on both flanks and the near tower hid the craft
  (`phaseC_first_blockout_near_tower_hid_craft.png`).
- Four models commissioned through the Meshy API from the blockout's
  proportions (`Scripts/submit_meshy_station_dress_v010.ps1`; v009 refused
  itself at the 800-character prompt cap before spending; 80 credits,
  4/4 succeeded; contact sheet `phaseC_meshy_v010_contact_sheet.png`),
  exported at declared sizes (`Tools/export_meshy_glb_v001.py`) and
  imported with Nanite, every size verified within 3 %
  (`Saved/Audits/Spacecraft/station_dress_import_v001.json`).
- The keys had to be promoted past the presenter's allow-list gate before
  any of them appeared; the log's "station mesh bound" lines prove all
  four load.
- Frames: `phaseC_meshy_towers_entry.png`, `phaseC_meshy_tower_promoted_station.png`.
- Commits 892e7b2, e85b97c.

## Phase D - the hero

- Entering the hall lands on the first OCCUPIED station, expanded 9 m for
  its tower and crew; the craft sits on its rams in the middle third of
  the free picture (`phaseCD_hero_framing_tower_blockout.png`,
  `phaseE_hero_with_fill.png`).
- The sortie carries the station's actual part mesh at a third of its
  size rather than a crate. Coded and tested; not yet seen on a frame.
- Commit 892e7b2.

## Phase E - fill the frame

- First placement (racks on the walls, lights over the storage zones) was
  off screen: the hall is 260 m by 180 m and the entry frame covers the
  middle 120 m. The fill lives beside the line now: racks in Crate.Tan in
  two runs along it, light bars in indicator white in a row behind it at
  9 m, where they sit above the craft on screen and never between the
  camera and it.
- Frames: `phaseE_tinted_racks_lightbars_entry.png`, `phaseE_hero_with_fill.png`.
- Commit e85b97c.

## Phase F - motion, then film

- Motion already existed (crane trips, sorties, fitting bursts, the
  departure); A to E made it visible.
- Film-ready state: `Saved/SaveGames/Film.sav` - a running line with the
  Coastal Rescue and Deep Reach contracts accepted and three craft in
  work. Copy it into the packaged game's save folder to start there.
- Packaged build: cycle 12, `Builds/LookPlan_2026_09_02` (see the status
  line at the end of this document for whether it completed).
- Filming is the owner's: a third of what the concept form judges is a
  player using the interface, and only he sees the game move.

## Tests

`Automation RunTests LineBoss.Spacecraft`: 138 tests, all Success, 0
failed, on every build of the day (`Saved/Automation/PhaseA*_2026_09_02`,
`PhaseC1`, `PhaseCD`, `PhaseCE`, `PhaseE`, `PhaseE2`, `PhaseE3`,
`AudioGC`, `AudioGC2`, `Hazard`, `Pacing2`). A correction to the day's
commit messages, which quoted the report's `succeeded` counter as
"116/116": that counter excludes tests that pass with a logged warning
(22 of them, 24 after the pacing retune, which makes two more tests log
"no contract demands a craft" because the faster line finishes its order
sooner). The honest figure is 138 pass, 0 fail throughout; the one red
run, `Pacing_2026_09_02` (1 fail), was the stranded-craft test whose
planted deadline no longer fell inside the build time, and it went green
once the deadline followed the retune.

## Not proven

- The primer coat and the hero framing are seen in PIE, not yet in the
  packaged build.
- The sortie IS on a frame now (`phaseD_sorties_station3_eight_frames.png`:
  eight frames at station 3 with a craft in work, a drone on its tether
  carrying a load to the hull, the crane taking the craft on in the
  seventh). The load is the crate fallback, not the pallet part: that
  station showed no stock stack for the carry to copy. The real-part
  carry is coded and tested but still not seen. A later pass added a
  fallback to the station's own kit pallet when no stock stack shows;
  the load on the tether is still a small pale block at the play zoom
  (`phaseD_sortie_load_station2.png`), which may be the pallet mesh at a
  third of its size or the crate - the frame cannot tell them apart, so
  this stays not proven.
- The tool tower reads mostly as its top from the play camera; whether a
  lower-angle silhouette is worth a camera change is a question for the
  owner, not something this pass decided.
- Warmth is still short of Car Manufacture's; the palette's neutral-sun
  evidence was respected and only a mild warm key applied.
- No frame was judged beside a reference screenshot side by side; each was
  judged against the morning's judgement frame. That is a weaker bar than
  the plan set.

## The packaged crash, and its fix

Cycle 12's first package (`Builds/LookPlan_2026_09_02`, BUILD SUCCESSFUL)
crashed about a minute into the replay: EXCEPTION_ACCESS_VIOLATION in
FAudioDevice::PlaySoundAtLocation under PlayWorldCue from TickHallCrane
(`Builds/LookPlan_2026_09_02/Windows/LineBossCarFactory/Saved/Logs/
LineBossCarFactory-backup-2026.09.02-13.17.48.log` and the log after it).
The cause is the same family as the mesh-cache purge of 2026-09-01: the
presenter's sound cache (`SoundByRole`) and its two audio component
handles carried no UPROPERTY, the editor kept the sounds alive, the
packaged game's garbage collector did not, and the audio device was handed
a freed sound. All three are reflected now; the suite run for that build is
`Saved/Automation/AudioGC_2026_09_02`. The lesson is the one already on
record: every cached UObject pointer in the presenter is a UPROPERTY, no
exceptions, and only a packaged soak finds the ones that are not.

The first replay also showed the Development build's "LIGHTING NEEDS TO BE
REBUILT (1 unbuilt object)" banner - cosmetic in Development, hidden in
Shipping, and not fixed here.

## The side-by-side, done after all (evening)

Our hero frame beside a Car Manufacture store screenshot
(`Saved/Audits/LineLook_2026_09_02/side_by_side_car_manufacture_vs_ours.png`;
the reference is viewed for judgement only and is not reproduced in the
docs). What theirs has that ours still lacks, in order:

1. **Warmth.** Their floor is a warm tan; ours reads cool grey under the
   neutral sun. The A/B frames (`warmth_ab_sun_0_05_1.png`, console
   `LB.Look.Sun 0..1`) show that a warmth of 1 gets the floor to a warm
   79/75/68 sample; the decision is the owner's against the palette's
   neutral-sun evidence.
2. **Saturated product.** Their cars are vivid red, blue and orange in
   every frame; our craft is white unless a coloured contract is running.
   The livery system exists; the demo state must carry coloured contracts
   (`Film.sav` does).
3. **Density.** Fifteen stations, people and machines in their frame
   against our five stations in a hall built for far more. The fill
   beside the line helps; the hall's size is a fixture decision on record.
4. **Hazard tape.** Their yellow bay outlines are bright and wide; ours
   are dim under the locked exposure. Cheap to widen and lift.

## Pacing, measured

Dev line, parts pre-stocked, sim time from Start to Dispatched on one
craft, at 4x wall speed (`Saved/Audits/LineLook_2026_09_02/pacing_first_ship.txt`):
intake reached at 12 s, material processing 116 s, hull fabrication
192 s, component fabrication 268 s, assembly staging 348 s, assembly
424 s, testing 472 s, dispatched 552 s. Nine minutes of sim for one craft,
of which the visible line work (assembly) is 48 s and the test 80 s; the
five OFF-LINE stages before the line take 400 s while nothing the player
can see happens. That is the first-ten-minutes problem in one number.

**Retuned the same evening.** The Scout's nominal cycle seconds drop from
440 to 255 (12/25/50/40/18/65/45; the Cargo keeps its heavier numbers),
the coordinator test's cycle total follows. Same measurement afterwards:
dispatched at 360 s of sim instead of 552 - six minutes for a first craft
on the dev line, so with the player's own building and buying time a
first ship lands inside ten. The remaining overhead is per-stop: crane
trips and admission waits between the six stations, roughly 100 s of the
360. Evidence: `pacing_first_ship.txt`, both runs.

## The warmth decision

Shown the A/B frames, the owner chose warmth 1: "yeah I agree with the
car manufacturer feel". The key light is warm by default now (the
console lever stays for future A/Bs); the palette adoption's neutral-sun
paragraph is superseded by that decision and says so in the presenter.

## The evening's tidy pass ("keep improving")

Owner, offered a fresh package: "no just keep improving, it's got to be
a lot better before the filming". So, off the current frame:

- Hall entry framing margin 1.35 to 1.2, so the racks and light bars sit
  at the picture's edges instead of bare floor.
- The fitting station's build-menu tile was blank once its portal went;
  it shows its tool tower now. The storage rack's tile was blank because
  the silo mesh it pointed at never existed on disk; it wears the Meshy
  pallet rack, promoted past the allow-list, and the rack lies along its
  bay's long side (long dressing meshes take a quarter turn when the
  footprint and the mesh disagree about which axis is long).
- Kit crates read as black blocks from the play camera because the lid
  was the dark tone; lid and body swapped.
- The storage rack's footprint turns from 10 by 6 to 6 by 10 so a rack
  placed at the default yaw presents its long side to the camera; the
  light bars move from the far flank at 9 m to directly over the line at
  11.5 m every 18 m, where a 35-degree camera projects them 16 m behind
  the line on screen and they never sit between the camera and anything
  (on the far flank they were the first thing in front of a watched
  rack).
- Frames: `tidy_entry_tiles_station.png`, `storage_rack_tile_and_floor.png`,
  `tidy_rack_facing_camera_bars_over_line.png`.

## Nothing sits on the line (owner, same evening)

"Make sure nothing blocks the line like drone charging docks etc." Once
every fitting station turned its long side along the line, the service
furniture laid out at the pad's ends - the crew's charging docks, the
eight slot pads, the cable runs, the kit dolly, the stockpile stacks -
stood in the track corridor between stations. All of it moved to the
flanks: the near flank (camera side, low things only) takes the docks in
a row outside the pad edge, the slot pads in a row inside it, the cable
runs and the cabinet; the far flank takes the tool tower at its upstream
corner and the kit dolly along the rest, with the hull sections lying
along the line; the stockpile stands beyond the far flank. Pallet meshes
turn a quarter to lie along the new axis. The rule is on record for
every future station-side element. Frame:
`nothing_on_the_line_flanks.png` (entry, a station gap, the rack).

Seen on the same frame and done next: at the FIRST station the craft had
no hull yet and its loose sections lay still. Those sections turned out to
be the craft's own "stripped hull" (a 2026-08-30 feature), not the dolly
pallets; they now start the stop spread apart along the craft's axis and
close up nose-to-aft as the stop progresses, and the real hull takes over
the instant it is fitted. The first pass laid them along local Y, which
put the loose hull ACROSS the line
(`hull_sections_closing_across_the_line_first_pass.png`); the assembled
hull runs along local X with the nose at -X, so the sections do too now
(`hull_sections_close_up_over_first_stop.png`, six frames ten seconds
apart). A dead first attempt that animated dolly pallets was removed.
The dolly then still carried its own set of hull section pallets beside
the craft's, two hulls in the picture; the hull is not a pallet on the
dolly any more (`hull_sections_one_set_dolly_without_hull.png`).

## The runway, the payoff shot (evening)

The departure is the loop's payoff and its frame was the weakest in the
game: a pale strip on pale paving, invisible, the departing craft a speck
in a 300 m frame (`departure_runway_before.png`). The strip's deck is
tinted asphalt-dark now with dark shoulders above the paving (the deck
block first went in at floor height and was buried under the site tiles,
the hall slab's lesson again), and the runway camera frames the strip
itself, 140 m, centred on it (`departure_runway_after_dark_deck.png`).
The runway test's part count moves from 85 to 86 for the deck. The craft
was then found never to cross the strip at all: the departure started
from the dispatch position, slid sideways to the runway's X and sprinted
from wherever it stood, in 4.8 s. It now taxis to the strip's START
during a 4.5 s chicane (a new approach term in the departure maths, zero
by default so the pinned tests hold) and sprints 7 s down the runway,
flames lit, shadow on the paving (`departure_taxi_arrives_at_strip_start.png`,
`departure_slowed_taxi_and_sprint.png`, six frames across the run). The
test that waits for a departure to finish waits 14 s instead of 8.

## The evening, in order (after "keep improving")

Each landed as its own commit with a frame and a green suite:

1. Warm key as the default (the owner's choice from the A/B frames).
2. The Scout's cycle seconds retuned 440 to 255; first ship at 360 s of
   sim on the dev line, was 552.
3. Tidy pass: tighter entry framing, the fitting station's build tile,
   the storage rack's real mesh and its footprint turned to face the
   camera, kit crate lids in tan, light bars over the line.
4. Nothing sits on the line: docks, slot pads, cable runs, dolly and
   stockpile moved from the pad's ends to its flanks.
5. The hull comes together at the first station, along the craft's axis,
   centred on its slot, with no second set of sections on the dolly.
6. The research tab as picture tiles; contracts you hold as cards.
7. The runway reads (dark deck, framed strip) and the departure taxis to
   the strip's start and sprints down it slowly enough to watch.

Cycle 13 (`Builds/LookPlan_2026_09_02c`) packages all of it; the status
line below says whether it completed.

## The second side-by-side (late evening)

Ours beside the same Car Manufacture screenshot after the evening's work
(`side_by_side_car_manufacture_vs_ours_evening.png`). Three faults, fixed
in one pass: still a stop darker than theirs (exposure multiplier 21 to
16, floor now 107/102/95); the craft on the line carried no visible
colour before the booth (the primer is 30 % toward grey, was 50 %); and
their conveyor is the picture's spine where our track was a thin line (a
dark corridor band with hazard edges now runs under the whole line -
paint, so nothing sits on it). What remains beside theirs: density, and
that is the hall's size; and the crowd, which for us is drones.

## Status

**Packaged playable, cycle 13** (`Builds/LookPlan_2026_09_02c`, BUILD
SUCCESSFUL). The packaged replay with real OS input
(`Saved/Audits/LookPlan_Package13_2026_09_02/`: thirteen frames over 3 m
48 s of sim, the UAT tail and both scripts) ran the dev line, the
Contracts tab with the livery cards and a held-contract card, the Build
tab and the running line - warm key, dark floor, racks, towers, the hull
coming together at station 1 - and the packaged log holds no fatal error.
`Film.sav` rides in the package's SaveGames. Same caveats as 12b: the
replay uses the dev Enter with an explicit zoom, which frames the hall's
west edge rather than the line's centre.

Earlier that day: **cycle 12b** (`Builds/LookPlan_2026_09_02b`, BUILD
SUCCESSFUL, 2.9 GB archive). The packaged replay with real OS input
(`Saved/Audits/LookPlan_Package12b_2026_09_02/`: thirteen frames over 3 m
48 s of sim time, the UAT tail and both scripts) ran the dev line, the
Contracts tab with the three livery cards, the Build tab, and the running
line with racks, towers and the dark floor, and the packaged log holds no
fatal error. The audio crash of cycle 12 is not reproduced. `Film.sav`
is copied into the package's own SaveGames folder by the replay script.

Not covered by the replay: the player's own hall entry (the replay uses
the dev Enter with an explicit zoom, which framed the hall's west edge
rather than the line's centre), the primer coat in the package (the
dev-started craft carries a white livery), and any run longer than four
minutes. The Windows Firewall prompt appears once for the new build path;
the replay dismisses it with Cancel, which changes no setting.
