<!-- COMMISSIONED BRAND SPEC, PRESERVED VERBATIM.
     Extracted from the owner's design-tool export on 2026-08-29.
     The source zip keeps ONE filename and has already been
     overwritten three times, so the only durable copy is this one.
     This is the AUTHORITY for colour, layout and motion; it
     supersedes the 'brand is OPEN' note in CLAUDE.md. Text is the
     tool's own wording - do not edit it to fit the code; if the
     code disagrees, the code is what changes, or the disagreement
     goes back to the next revision as an amendment. -->

Implementation spec · rev C

 Grid · panels · six screens · type · loc · motion

 Layout and motion, for a UI that must not eat the factory

 Everything is px at 1920 × 1080, the authoring resolution. The governing constraint of this document is the frame: at FOV 48 and pitch −35 the player is watching a live diorama, so the interface has a hard area budget and a protected centre. Two amendments to rev A/B fall out of the 8px grid and are stated at the end.

 4A

 Spacing scale and grid

 ONE SCALE · BASE 4 · EVERY PANEL DIMENSION A MULTIPLE OF 8

 STEP
 PX
 THE ONE PLACE IT APPLIES

 s1
 4
 Inside a single control: icon-to-label, chip-to-text, value-to-unit, pip spacing.

 s2
 8
 Between siblings in a group: list rows with no rule, tile gutters, button-to-button, stacked banners.

 s3
 12
 Clearance around a rule — 12 above, 1px rule, 12 below. Also body padding on the 256 panel.

 s4
 16
 Panel body padding (default), header and footer horizontal padding, banner padding.

 s5
 24
 Between groups that are not separated by a rule. Never both a rule and s5.

 s6
 32
 Viewport margin, and the gap between two docked panels on the same edge.

 s7
 48
 Inside the launch summary card only — the one place the UI is allowed to breathe.

 Rules. No value outside the scale — 20, 28 and 36 are illegal. Every panel width, height, header, footer and row height is a multiple of 8; text baselines land on 4. One role, one step: if two panels use 12 and 16 for the same job, their docked left edges go ragged and rows stop lining up across panels, which is the visible failure.

 GRID — NO FLUID COLUMNS, FOUR PANEL WIDTHS

 PITCH 8px master pitch everywhere. Tile pitch 56 (48 tile + 8 gutter). Row heights 32 / 40 / 48. Header 40, footer 56, top strip 44. 

 WIDTHS 256 build menu / objectives · 424 status, inspector, banner dock · 560 contract list · 720 launch summary card. Nothing else. A fifth width is how a UI starts drifting. 

 256 DERIVED 2 edge + 16 pad + (4 × 48 tiles + 3 × 8 gutters = 216) + 16 pad + 2 edge = 252, rounded to 256 with the 4px slack held at the inner right edge. This is why the icon gutter changes to 8 (amendment 2). 

 SNAP Panels snap to viewport edges at s6 = 32px margin, never to each other's centres. A panel's height is content-driven and rounded up to 8. 

 SCALING — FIXED PX, STEPPED SCALE, WORLD TAKES THE SURPLUS

 1920×1080 Scale 1.00. The authoring case. 

 2560×1440 Scale 1.25 — every value on the scale stays integral (4→5, 8→10, 48→60, 56→70) and 13px type becomes 16px. Applied as a single UMG DPI Scale curve, not per-widget. 

 21:9 Scale follows height only. 2560×1080 stays at 1.00; 3440×1440 at 1.25. Panels keep their px width and the extra 640–880px of width goes entirely to the world — the correct payoff for an ultrawide in a diorama game. 

 USER SCALE 0.90 / 1.00 / 1.15 / 1.30 multiplied onto the resolution scale. Below 0.90 the 13px roles fall under the 12px floor; above 1.30 the area budget below is breached at 1080p. 

 WHAT BREAKS Fluid panels: at 21:9 a stretched status panel gives 1100px rows with 40 characters in them and the dead space reads as a bug. Integer-only (1× / 2×): 1440p gets no benefit at 1× and is unusable at 2×. Per-widget scaling: rounding drifts between siblings and the 8px grid dies. 

 4B

 Panel anatomy, and how it sits over the world

 PARTS TO SPEC · SHOWN AT 388 IN A 424 COLUMN

 STATION 05 — RCS CLUSTER

 04

 Cycle time 18.4 s 

 Uptime 96.2 % 

 Throughput 142.06 /hr 

 Cold-gas tank 2 

 Thruster nozzle 8 

 Harness loom 0 

 INSUFFICIENT RESOURCES
 AssemblyRobot-002 needs 1× Component.Hull

 REASSIGN

 PAUSE

 PARTS, HEIGHTS AND TOKENS

 PART
 SIZE
 TOKENS

 Edge
 2px
 Panel.Edge #0E0E0E on all four sides, border-box. The only "elevation" in the system.

 Header
 40px
 Panel.BgRaised fill, 16px h-padding, 1px Panel.Rule bottom. Title Text.Heading; optional right-hand count Text.Value.

 Body
 auto
 Panel.Bg, 16px padding (12 on the 256 panel). Rows 32 (dense list) / 40 (standard) / 48 (with 32px icon), 8px between rows.

 Group rule
 1px
 Panel.Rule with 12px clearance above and below. Groups are separated by a rule or by 24px, never both.

 Banner slot
 auto
 Directly above the footer, per rev A §2: fixed top edge, grows down, list region absorbs it.

 Footer
 56px
 Panel.BgRaised, 1px Panel.Rule top, 16px h-padding. Buttons 32px tall, labels flush left, 8px apart. Max 3 buttons; a fourth becomes an overflow row.

 Scrollbar
 4px
 Text.Dim thumb on a 1px Panel.Rule track, inside the padding. Always visible when scrollable — a hidden scrollbar hides information in a management game.

 OPAQUE — AND WHAT TRANSLUCENCY WOULD COST

 Panels are fully opaque. The hue-free palette buys its legibility from a fixed 14:1 contrast between Text.Body and Panel.Bg; that number only exists because nothing moves behind the text. Amber machinery passing under a translucent panel drops worst-case contrast to about 9:1 and, worse, casts a warm tint the hue-free UI has no defence against — and red-on-amber loses roughly a third of its perceived separation, which is the one thing rev A protects.

 The world stays visible by area, not by transparency. Three mechanisms: the area budget below; every panel collapses to a 32px rail on double-click of its header or Tab ; and all non-essential panels auto-collapse for the duration of a launch, restoring afterwards.

 The only legal translucency in the game is the modal scrim: #0E0E0E at 62% alpha , no blur. If you ever do want a translucent panel, the bound is 92% alpha with a 6px background blur and it may not contain a refusal banner.

 DOCKING, THE STAGE RECT, AND THE AREA BUDGET

 STAGE RECT · 52% × 60%

 TOP STRIP 44 · LEFT 256 · RIGHT 424 · BANNER DOCK 424
MARGIN 32 · STAGE RECT NEVER COVERED EXCEPT BY A MODAL

 TOP 44px full-width strip: credits, date and speed controls, objective count. At pitch −35 the top ~15% of frame is distant background, so this is the cheapest real estate in the game. 

 LEFT 256 build menu, top-anchored, max 70% of viewport height. Left because the player builds left-to-right along the line. 

 RIGHT 424 context column — production status, station inspector or contract list (560 pushes the stage rect; see below). One panel at a time, never two stacked. 

 BOTTOM-LEFT 424 dock for a refusal raised from the world rather than from a panel, and for the selected-entity action bar. 

 STAGE RECT The centred 52% × 60% of the frame (998 × 648 at 1080p) is protected: no panel, tooltip, banner or toast may enter it. Only a modal may, and only the launch summary and settings are modals. 

 BUDGET ≤ 28% of frame area in normal play, ≤ 40% with an inspector open. Worked: top strip 1920×44 = 84,480 + left 256×604 = 154,624 + right 424×800 = 339,200 → 578,304 of 2,073,600 = 27.9% . The 560 contract list replaces the 424 at its stated geometry — 9 rows × 44 + 40 header + 56 footer + 32 padding = 524px tall — giving 84,480 + 154,624 + (560 × 524 = 293,440) = 532,544, or 25.7% . That is why its height is capped at 524 and why it may never open alongside the inspector: at the right panel's full 800px height a 560 panel lands at 33.1%. 

 IF CROSSED Past ~35% the game reads as a spreadsheet with a diorama in the corner — the exact failure mode of the benchmarks, and unrecoverable in a screenshot or a trailer frame. 

 4C

 The six screens, and a density rule

 THE DENSITY RULE — FOUR NUMBERS, CHECKABLE ON ANY PANEL

 1. Whitespace 12–28% of panel body area. Under 12% is cramped and unscannable; over 28% is the "unfinished game" read you are worried about. Measure padding + gaps + empty rows against body area; it is a five-minute check per panel.

 2. 2.2–3.0 rows per 100px of body height — i.e. an average row pitch of 33–45px. Denser than that and 15px condensed type starts touching; thinner and the panel is padding pretending to be content.

 3. Every row carries ≥ 2 facts (label + value, or label + state). A row with only a label is a heading, and a panel of headings is a menu, not a management UI. Groups hold 3–7 rows; a 2-row group merges upward.

 4. One panel, one question , max 3 groups and 1 numeric column. If a panel needs a second numeric column it is two panels, or a table — and a table belongs in the 560 width.

 1 · SITE MAP

 CONTENTS Top strip (credits · date/speed · objectives count). Left 256 build menu: 5 category rows, tiles 4-wide. Right 256 objectives panel, collapsed by default, 3–5 rows when open. Nothing else. 

 DENSITY Deliberately the thinnest screen in the game — ~19% occupancy. The 600 × 600 m plot is the content here, and a busy site map fights the one screen that has to sell scale. 

 REFUSAL Bottom-left 424 dock (placement came from the world, not a panel). Offending building outlined in State.Refusal. 

 2 · FACTORY INTERIOR

 CONTENTS Same top strip. Left 256 station build menu. Right 424 production status, in this order: current contract (livery chip, craft tier, completion, deadline — 4 rows), rule, line throughput (units/hr, cycle, bottleneck station — 3 rows), rule, station list (max 7 visible, then scroll). 

 DENSITY The densest routine screen: 14 rows, 3 groups, ~24% whitespace, 27.9% occupancy. This is the ceiling — if a fourth group is needed, it goes in the inspector. 

 REFUSAL Bottom of the right panel, above its footer. Station list scrolls to absorb the height. 

 3 · CONTRACT LIST

 CONTENTS Right-docked 560, not a modal — accepting work while watching the floor is the point. Row 44px, six columns at fixed x: chip 12 · customer (flex) · craft tier 72 · payment 96 right-aligned · deadline 88 · accept 88. Max 9 rows visible, then scroll. Header carries the count. 

 DENSITY One group, one numeric column, 44px rows: 2.3 rows/100px. The exception to "max 3 groups" — a list is a single group of arbitrary length. 

 REFUSAL Above the footer of this panel (e.g. accepting a fourth concurrent contract). May not open alongside the inspector — see the area budget. 

 4 · STATION INSPECTOR

 CONTENTS Replaces production status in the right 424 (never stacks with it). Header: station name + 32px type icon. Groups: rate (cycle time, uptime, throughput), rule, stock (3–7 part rows with counts; zero rows in Text.Disabled), rule, assignment (assigned parts, drones). Footer: Reassign / Pause / Demolish. 

 DENSITY 3 groups, 9–13 rows, one numeric column right-aligned at a fixed x shared with production status — so switching panels does not move the numbers. 

 REFUSAL Above the footer; the stock group is the scrolling loser. This is the most common refusal site in the game. 

 5 · REFUSAL BANNER — PLACEMENT TABLE

 ONE RULE The banner appears in the panel that owns the action. If the action came from the world (a click on a station, a placement attempt), it appears in the bottom-left 424 dock. Never both, never two banners. 

 BUILD MENU A refused build attempt does not banner from the 256 panel — it is too narrow for a headline plus detail. It banners in the bottom-left dock, and the tile takes its refused state (rev B 3B). 

 NEVER Never in the top strip, never centred, never inside the stage rect, never as a floating toast. 

 DURING LAUNCH Panels auto-collapse for a launch, but a live refusal keeps its dock open — a launch does not get to hide a fail-closed state. 

 6 · LAUNCH SUMMARY

 PLACEMENT Bottom-anchored 720 card, not a centred modal. The top 62% of the frame stays clear so the ship is still in shot — the summary may never cover the launch it is summarising. Scrim at 62% below the card's top edge only. 

 CONTENTS Livery chip at 16px + customer, craft tier, payment, on-time bonus or late penalty, time on line, units this shift. Four to six rows, s7 = 48px padding, one primary action. No charts, no confetti. 

 TIMING Appears when the craft clears the chicane, not at wheels-off. No auto-dismiss: Enter , Esc or click. It does not pause the sim. 

 DENSITY The one low-density surface in the game — ~40% whitespace, deliberately outside the density rule. It is the reward beat; everything else is the work. 

 4D

 Type, applied — role to size, weight, colour

 ROLE
 FACE
 SIZE
 WEIGHT
 TRACK
 LINE
 COLOUR TOKEN

 Top-bar readout
 Plex Sans Cd
 20px
 SemiBold
 0.02em
 24px
 Text.Value #FFFFFF

 Panel heading
 Saira Condensed
 13px
 SemiBold
 0.18em
 16px
 Text.Heading #A8A4A1

 Group heading
 Saira Condensed
 12px
 SemiBold
 0.18em
 16px
 Text.Dim #918D8B

 Row label
 Plex Sans Cd
 15px
 Regular
 0em
 20px
 Text.Body #EDEDEC

 Numeric value
 Plex Sans Cd (tabular)
 15px
 Medium
 0.01em
 20px
 Text.Value #FFFFFF

 Unit
 Plex Sans Cd
 13px
 Regular
 0em
 20px
 Text.Dim #918D8B

 Secondary text
 Plex Sans Cd
 13px
 Regular
 0em
 18px
 Text.Dim #918D8B

 Disabled row
 Plex Sans Cd
 15px
 Regular
 0em
 20px
 Text.Disabled #5E5B59

 Button label
 Saira Condensed
 14px
 SemiBold
 0.10em
 16px
 Text.OnPositive / Text.Body

 Refusal headline
 Plex Sans Cd
 13px
 SemiBold
 0.08em
 18px
 #FFFFFF on State.Refusal

 Refusal detail
 Plex Sans Cd (tabular)
 13px
 Regular
 0em
 18px
 Text.Body on #2A1A17

 Minimum shippable size at 1080p is 12px (group headings and nothing else). 13px is the floor for anything read continuously; 11px is illegal — at 15px condensed row labels, an 11px unit beside them reads as a rendering artefact. Two more rules: no more than three sizes in one panel, and the tinted refusal detail ground #2A1A17 is the only surface in the UI besides the banner that is not a pure neutral — it is a 7% mix of State.Refusal into Panel.Bg, and it exists so the detail line stays attached to its headline when the list above it scrolls.

 4E

 Localisation resilience — +35% without reflow

 FIXED WIDTHS, GROWING HEIGHTS

 PRINCIPLE Panels never widen. Width is bound to the area budget and the stage rect, so a widening panel would move the protected centre of the frame. Panels grow down , and rows grow taller . 

 MAY REFLOW Row labels (wrap to 2 lines, row 32 → 52). Button labels (wrap to 2 lines, button 32 → 48; a third line means the string is wrong). Refusal detail (unbounded). Tooltips (max 320px wide, unbounded height). Objective text. 

 MUST NEVER MOVE Panel outer edges. The numeric column's right edge. The top strip's element order and x-positions. Tile grid pitch. The stage rect. Footer button order. 

 HEADINGS Single line, never wrap, never truncate — enforced by a 28-character loc budget, the same mechanism as the refusal headline. A heading that needs two lines is a heading that is trying to be a sentence. 

 BUILD GATE Lay out against a pseudo-locale at +40% string length (5 points of headroom over your 35% estimate) and fail the build on any clipped or truncated widget. Verify at 1280×720 too: same panels, 25% less height, so every wrap costs a visible row. 

 NUMERIC COLUMNS ACROSS LOCALES

 STRUCTURE Three fixed columns, right to left: unit (40px, left-aligned), value (right-aligned to a fixed x), label (flex, wraps). Putting the unit in its own column is what stops the number's right edge from moving when "s" becomes "с" or "/hr" becomes "/ч". 

 WIDTH RESERVE Reserve the value column for the widest grouping form of the widest expected magnitude — thin-space grouping ("1 234 567", RU/FR) is wider than comma grouping at the same digit count. Compute the reserve once from the tabular advance width × (digits + separators), never from the current locale. 

 FORMATTING All grouping and decimal marks from ICU locale data via FText::AsNumber — never hand-built strings, never a hard-coded comma. Negatives take a leading minus inside the reserved width; percent and currency marks live in the unit column. 

 NEVER Never centre a number, never proportional figures, never a per-locale column width, and never re-measure the column at runtime — a column that resizes as digits tick is the jitter the tabular instance exists to prevent. 

 4F

 Motion — the world moves, the interface does not

 Your instinct is right, and it has two reasons behind it. At pitch −35 with drones, arms and conveyors in constant motion, any moving UI element competes for the same attention the factory is asking for — motion is the strongest signal you have, and it is already spent. Second, this loop is read → decide → click, dozens of times a minute; animation is latency the player pays on every one of those.

 NEVER ANIMATES

 Numbers. No count-ups, no tweens. A tweening number is wrong for the length of the tween, and the player is reading rates.

 Rows and lists. No slide-in, no stagger, no reorder animation. Content appears in place.

 Icons and tiles. No idle motion, no hover scale, no pulse. Hover is an instant fill swap.

 Scrolling. 1:1 with the wheel, no inertia, no easing, no smooth-scroll.

 The refusal text. It never moves, fades in or slides. Movement is what makes a message feel like a toast, and toasts get ignored.

 Also never: parallax, panel drop shadows animating, progress-bar easing (fills are linear and sim-driven), screen shake, red vignette, world desaturation behind a panel.

 THE FIVE TRANSITIONS THAT EXIST

 WHAT
 DURATION
 CURVE / PROPERTY

 Panel open
 120 ms
 Ease-out (0.2, 0, 0, 1); opacity 0→1 plus 8px translate along the dock axis. No scale.

 Panel close
 90 ms
 Linear opacity only, no translate. Closing should feel like it already happened.

 Panel content swap
 status → inspector 
 80 ms
 Opacity dip to 0.35 and back, no movement — the frame stays put so the player's eye keeps its place.

 Site → interior
 420 ms
 Camera dolly, ease-in-out (0.4, 0, 0.2, 1). UI sequence: outgoing panels close at t=0 (90 ms), incoming panels open at t=300 ms — no panel moves while the camera moves . The top strip persists untouched and is the anchor that makes the cut legible.

 Value change
 160 ms
 Digits swap instantly. A 1px Text.Dim underline flashes beneath the value — only for player-caused changes, max once per 500 ms per value. Continuously ticking values (timers, rates) never flash; flashing those is the annoyance failure.

 Tooltip
 350 ms delay
 Then appears instantly at full opacity. No fade, no follow-the-cursor.

 THE REFUSAL ARRIVAL — IMPOSSIBLE TO MISS, SURVIVABLE FIFTY TIMES

 FRAME 0 The banner is simply there , full opacity, final position. No slide, no fade, no scale. Appearance is instant because instant is what reads as a system response rather than a notification. 

 ATTENTION A value pulse, not a motion pulse: the 2px keyline goes #FFFFFF for 80 ms, back to #EC3013 for 80 ms, once more, then holds. Total 320 ms , two beats, nothing moves a pixel. 

 WORLD ECHO The named entity's 2px State.Refusal outline appears on the same frame and pulses on the same 80 ms beats, so the player's eye is told where as well as what. 

 SOUND One 60 ms non-musical click, −18 dB, no rising tone and no stinger. Suppressed by the same rules as the pulse. 

 REPEAT RULE 1 Same reason code + same entity within 4 s : the banner updates but does not pulse. This is the click-again case, and it is the whole reason the fiftieth refusal is not annoying. 

 REPEAT RULE 2 Same reason code ≥ 3 times in 10 s : pulse and sound are suppressed entirely until 10 s of silence. The player is holding the mouse button; they know. 

 DIFFERENT CODE Always pulses, even inside the suppression window — a new reason is new information. 

 DISMISSAL None. It persists while the condition holds and clears in one frame when resolved — no fade-out, because a fading refusal implies things are fine slightly before they are. 

 IF CROSSED Longer than ~400 ms of pulsing, or any movement, and the banner becomes a toast: at fifty repeats the player learns to ignore it, and the fail-closed design — which is the whole game's explanation mechanism — stops working. 

 TWO AMENDMENTS TO REV A / REV B — BOTH FALL OUT OF THE 8PX GRID

 1. Panel width 422 → 424, refusal content width 390 → 392. Rev A derived 422px from "22% of 1920". 422 is not a multiple of 8, so a 422 panel puts every row inside it off the master pitch and the icon tiles never align with the rows beside them. 424 is 22.08% of 1920, costs 2px of world, and keeps the whole panel on the grid. All rev A line-count figures survive: at 392px of content the ~34 chars/line measurement is unchanged, so 22 / 54 / 97 characters still give 1 / 2 / 3 lines.

 2. Icon tile gutter 4 → 8, tile pitch 52 → 56. Rev B specified a 48px tile with a 4px gutter, which is a 52px pitch — not a multiple of 8, so a tile grid drifts against every row and rule in the same panel. Gutter 8 gives a 56px pitch, 4 columns of tiles fit the 256 panel exactly (216px of tiles inside 16px padding, 4px of slack at the inner right edge), and the icon art, the 48px tile and the two-channel state treatments are all unchanged.
