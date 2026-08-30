# Sound spec — the audio shopping list (v001, 2026-08-25)

The game is currently silent; this is the complete first-pass asset
list, in wiring priority order. Sourcing: generate (AI audio tools),
buy (packs), or record — owner's choice per line. Formats: WAV 44.1 kHz
16-bit, loops seamless where marked. I wire and mix everything through
the same authority-mirroring discipline (a sound only plays when its
system state says so — audio never invents events).

## Priority 1 — the launch (the signature; wire first)

| Sound | Trigger (state) | Character | Length |
|---|---|---|---|
| RCS hover loop | Testing stage hover | airy pulsed thruster hiss | 8 s loop |
| Strobe arm clunk | strobes arming | heavy relay clack + rising whine | 1.5 s |
| Main engine ignition | throttle-up handover | deep concussive light-off | 2 s |
| Main engine sprint loop | sprint phase | layered rocket roar, doppler-friendly | 10 s loop |
| Chase-light race loop | tube chase active | fast electronic tick sweep | 2 s loop |
| Departure boom | craft exits the door | distant crack + long tail | 4 s |

## Priority 2 — the fleet (the co-stars)

| Sound | Trigger | Character | Length |
|---|---|---|---|
| Drone rotor loop | any drone flying | quad-rotor buzz, pitch-shiftable | 4 s loop |
| Drone launch | dock -> ToSupply | spool-up whir | 1 s |
| Drone dock/charge | landing + charging | settle thump + soft charge hum loop | 1 s + 6 s loop |
| Fitting laser loop | Fitting phase | focused energy hiss | 3 s loop |
| Weld sparks | spark bursts | crackling arc spits (3 variants) | 0.5 s each |
| Spray loop | painting pass | fine airless spray hiss | 4 s loop |

## Priority 3 — the factory bed (always-on ambience)

| Sound | Trigger | Character | Length |
|---|---|---|---|
| Hall room tone | always | vast quiet industrial air | 30 s loop |
| Station work loop | station crafting | machine-specific rhythm (one generic first) | 8 s loop |
| Belt run loop | belt with chase active | smooth roller glide | 6 s loop |
| Power plant hum | plant powered | deep fusion thrum | 10 s loop |
| Order arrival | delivery lands | freight thud + beep | 2 s |

## Priority 4 — UI voice (the fail-closed toasts made audible)

| Sound | Trigger | Character | Length |
|---|---|---|---|
| Click/confirm | any button | soft industrial tick | 0.2 s |
| Refusal | any fail-closed toast | firm double-buzz, not punishing | 0.4 s |
| Purchase | station/bay/belt bought | satisfying clunk + register chime | 0.8 s |
| Contract complete | settlement | restrained fanfare, pride not confetti | 2.5 s |
| Unlock | milestone reached | rising three-note reveal | 1.5 s |

## Music (separate decision)

One calm industrial ambient bed (~3 min loop) + one launch swell sting
(~20 s) is enough for EA. Defer style choice until the palette look is
final on screen; music is the last identity layer.

Count: 22 SFX + 2 music. Wiring plan: UAudioComponent per system,
volumes as config constants, all triggers read from authority state.
