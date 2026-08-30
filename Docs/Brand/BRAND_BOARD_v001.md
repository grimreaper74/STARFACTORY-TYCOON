<!-- COMMISSIONED BRAND SPEC, PRESERVED VERBATIM.
     Extracted from the owner's design-tool export on 2026-08-29.
     The source zip keeps ONE filename and has already been
     overwritten three times, so the only durable copy is this one.
     This is the AUTHORITY for colour, layout and motion; it
     supersedes the 'brand is OPEN' note in CLAUDE.md. Text is the
     tool's own wording - do not edit it to fit the code; if the
     code disagrees, the code is what changes, or the disagreement
     goes back to the next revision as an amendment. -->

Turn 2 — Refusal wrap & overflow

 Rules 2a · 2b · 2c 

 The refusal state at real panel width

 Panel is 22% of 1920 = 422px, so a banner has 390px of content width. At 11px mono with 0.1em tracking that is about 34 characters per line: a 70-character translation is two lines, and the worst cases — a reason plus the missing parts — run to three. Every panel below is drawn at true 422px. Three candidate rules; the shared writing and layout constraints are the same in all three.

 2a · BANNER GROWS, LIST SCROLLS

 NO CAP

 STATION 05 — RCS CLUSTER

 422 PX

 Cold-gas tank ×2 240 

 Thruster nozzle ×8 1,120 

 Avionics bay 860 

 Harness loom 310 

 INSUFFICIENT RESOURCES

 NICHT GENÜGEND RESSOURCEN FÜR DIESEN AUFTRAG VORHANDEN

 НЕДОСТАТОЧНО РЕСУРСОВ ДЛЯ ЗАВЕРШЕНИЯ КОНТРАКТА НА СТАНЦИИ 05 — ТРЕБУЕТСЯ БАЛЛОН ХОЛОДНОГО ГАЗА ×2

 22 / 54 / 97 CHARS = 1 · 2 · 3 LINES — SAME BANNER, HEIGHT FOLLOWS THE STRING

 The refusal is never truncated and never clipped: the banner block is auto-height, wraps on word boundaries, and grows downward. The part list above it is the flexible region and takes the loss — it scrolls, the banner does not. Panel height stays fixed, so nothing below the panel moves when a message appears.

 2b · TWO-LINE CONTRACT + DETAIL ROW

 CAP 2 LINES

 STATION 05 — RCS CLUSTER

 422 PX

 NICHT GENÜGEND RESSOURCEN

 Fehlt: Kaltgastank ×2, Kabelbaum ×1 — Auftrag 0417 an Station 05.

 НЕДОСТАТОЧНО РЕСУРСОВ

 Не хватает: баллон ×2, жгут ×1 — контракт 0417, станция 05.

 HEADLINE ≤ 32 CHARS IN EVERY LOCALE · DETAIL WRAPS FREELY BELOW

 Fixes it in the copy contract rather than the layout: the red headline is a short canonical reason with a hard 32-character budget written into the loc sheet, so it can never exceed two lines. Everything variable — quantities, part names, station number — moves into a wrapping detail row in the UI face, which is easier to read at length than tracked caps.

 2c · BANNER LEAVES THE PANEL

 2× WIDTH

 STATION 05 — RCS CLUSTER

 422 PX

 Cold-gas tank ×2 240 

 Thruster nozzle ×8 1,120 

 Harness loom 310 

 НЕДОСТАТОЧНО РЕСУРСОВ ДЛЯ ЗАВЕРШЕНИЯ КОНТРАКТА НА СТАНЦИИ 05 — ТРЕБУЕТСЯ БАЛЛОН ХОЛОДНОГО ГАЗА ×2

 ANCHORED TO PANEL EDGE · 640 PX WIDE · 97-CHAR WORST CASE = 2 LINES

 The refusal is not a panel element at all — it is anchored to the panel's outer edge and free to run to 640px over the floor, so even the 97-character worst case fits in two lines and the panel never reflows. Costs you a strip of the play area for a few seconds and needs a scrim or the hazard flash to stay legible over amber machinery.

 SHARED RULES
 APPLY TO ALL THREE 

 WRAP Word boundaries, overflow-wrap: anywhere as the fallback so a single unbroken compound (German, Finnish) breaks rather than overflows. No hyphenation dictionary. 

 NEVER No ellipsis, no clip, no shrink-to-fit on a refusal. A fail-closed message the player cannot read is a bug, not a layout compromise. 

 GROWTH Banner grows downward from a fixed top edge, so the first line does not move between the 1-line and 3-line cases — the player's eye lands in the same place every time. 

 STACKING One refusal visible at a time per panel; a second replaces the first. Line height 1.35, 8px between stacked messages, 10px 8px padding inside. 

 TEST STRINGS Ship a pseudo-locale at +60% string length and one ~100-character worst case through the build, at 1280×720 as well as 1920×1080 — at 720p the same 22% panel is only 282px and every case gains a line. 

 MIN WIDTH Below 320px of content width the panel switches to the 2b headline-plus-detail form regardless of which rule you pick — tracked caps stop being readable in three-line blocks. 

 Turn 1 — Identity exploration

 Wordmarks 1a – 1d · Palettes 1e – 1g · Type 1h – 1j 

 Star Factory Tycoon — brand directions

 Everything here is neutral by construction: graphite ink on pale ground, no owned hue. Colour is left to the liveries. Safety yellow appears only as factory-native structural striping, never as a logo colour, and each direction is shown at title size, at Steam capsule size and reversed on a dark panel.

 01

 Wordmark directions

 1a · PLANT SIGNAGE

 ARCHIVO EXPANDED 800

 STAR
FACTORY
TYCOON

 CAPSULE 231×87

 STAR FACTORY
TYCOON

 REVERSED

 STAR FACTORY
TYCOON

 Widest, heaviest, most industrial-signage of the four. Three flush-left lines make a solid block that survives the capsule crop. Reads factory before space. Longest translations get the most room here because the stack takes short lines.

 1b · WORKS PLATE

 SAIRA CONDENSED 700

 ASSEMBLY WORKS · LICENCE 0417

 STAR FACTORY
TYCOON

 CAPSULE 231×87

 STAR FACTORY
TYCOON

 REVERSED

 STAR FACTORY
TYCOON

 Condensed, so it holds far more characters per line — the safest choice for German and Russian. The rule and the licence line frame it as a manufacturing plate. Tallest x-height of the set, best small-size legibility.

 1c · CONTRACT MONO

 IBM PLEX MONO 600

 STAR FACTORY
 [ TYCOON ] 

 LINE 01 / STATION 09 / DELIVERED

 CAPSULE 231×87

 STAR FACTORY
[ TYCOON ]

 REVERSED

 STAR FACTORY
[ TYCOON ]

 The wordmark is the same face as the readouts, so the logo and the UI are one system — cheap to localise, and every bracketed contract tag in the game becomes brand. Coolest and most technical of the four; least "tycoon".

 1d · TYCOON SLAB

 BITTER 800

 Star Factory
Tycoon

 SPACECRAFT · BUILT TO ORDER

 CAPSULE 231×87

 Star Factory
Tycoon

 REVERSED

 Star Factory
Tycoon

 Slab serif buys warmth and commerce — ledgers, freight, business empires. The one direction that puts management first and space nearly last. Set in caps; the slabs thicken at small sizes, so this needs the most optical care in the capsule.

 02

 UI palettes — dark side panel over a bright floor

 Each panel sits on the same strip of factory floor — pale concrete, graphite machine, amber machine, safety striping — so you can judge the states against what is actually behind them. The three differ on one axis: how much hue the panel is allowed to spend.

 1e · INK & SIGNAL

 COOL GRAPHITE

 STATION 04 — HULL FIT

 RCS cluster ×4 AFFORDABLE 

 Avionics bay LOW STOCK 

 Cold-gas tank QUEUED 

 INSUFFICIENT RESOURCES

 NO PATH TO STATION 05

 CONTRACT EXPIRED

 1E2226
PANEL
 8D979F
HEADING
 E6E9EB
BODY
 4FD39A
OK
 A79BF0
WARN
 FF4A3D
REFUSE

 Warning is deliberately lilac, not amber — amber is machinery, so a yellow caution badge would read as a machine, not a message. Mint and lilac are the two hues furthest from anything on the floor; refusal keeps the conventional red.

 1f · BLUEPRINT

 INDICATOR BLUE

 STATION 04 — HULL FIT

 RCS cluster ×4 AFFORDABLE 

 Avionics bay LOW STOCK 

 Cold-gas tank QUEUED 

 INSUFFICIENT RESOURCES

 NO PATH TO STATION 05

 CONTRACT EXPIRED

 16202B
PANEL
 7F97AD
HEADING
 DFE9F2
BODY
 9FE3FF
OK
 D8B476
WARN
 FF2F6A
REFUSE

 Takes its hue from the blue-white indicator lights already in the game, so the panel reads as instrumentation. Refusal is a filled magenta-red bar — the loudest of the three options, and impossible to confuse with an amber machine. Warning is a low-chroma sand, kept dull on purpose.

 1g · MONO + ONE RED

 HUE-FREE PANEL

 STATION 04 — HULL FIT

 RCS cluster ×4 AFFORDABLE 

 Avionics bay LOW STOCK 

 Cold-gas tank QUEUED 

 INSUFFICIENT RESOURCES

 NO PATH TO STATION 05

 CONTRACT EXPIRED

 1B1B1B
PANEL
 9A9694
HEADING
 EDEDEC
BODY
 FFFFFF
OK (FILL)
 HATCH
WARN
 EC3013
REFUSE

 The strictest reading of your rule: the panel owns no hue at all. Positive is a white fill, warning is a dashed hatch, and red is the only colour in the interface — so a refusal is the single loudest thing on screen without the UI ever competing with a livery.

 03

 Type pairings

 All six faces are open-licence with wide Latin coverage including Cyrillic and Vietnamese where noted, so nothing here blocks localisation. Readout specimens are shown at 13px, the size a dense station list actually runs at.

 1h · ARCHIVO + PLEX MONO

 PAIRS WITH 1a

 CONTRACT BRIEF

 Archivo — variable width, 62–125. One family covers signage, headings and body.

 ST-04 HULL FIT 18.4 s 

 ST-05 RCS CLUSTER 07.9 s 

 THROUGHPUT / HR 142.06 

 0123456789 -$18,400 

 Widest tonal range: one heading family that can go from narrow labels to signage weight, against a mono with genuinely distinct 0/O and 1/l. Best for tables of numbers.

 1i · SAIRA CD + PLEX SANS CD

 PAIRS WITH 1b

 CONTRACT BRIEF

 Saira Condensed over IBM Plex Sans Condensed — both narrow, so long strings fit.

 Station 04 — hull fit 18.4 s 

 Station 05 — RCS cluster 07.9 s 

 Ressourcenmangel behoben 142.06 

 0123456789 -$18,400 

 The localisation-first pairing: both faces are condensed, so translated strings that would break a normal-width UI still fit the panel. Sentence case reads friendlier than the all-caps options.

 1j · CHAKRA PETCH + JETBRAINS

 PAIRS WITH 1c / 1d

 CONTRACT BRIEF

 Chakra Petch — squared-off, machine-cut, without tipping into sci-fi display.

 ST-04 HULL FIT 18.4 s 

 ST-05 RCS CLUSTER 07.9 s 

 THROUGHPUT / HR 142.06 

 0123456789 -$18,400 

 The most engineered voice — squared corners in the headings, a tall-x mono for readouts. Leans furthest toward machinery, so watch that it does not pull the game back toward generic sci-fi.

 IF YOU WANT ONE ROUTE

 1b + 1g + 1i

 The condensed works plate takes the most translated text, the hue-free panel keeps every colour on screen belonging to a ship, and both type faces are narrow enough for a dense side panel.

 If the capsule needs more shelf presence, swap the wordmark to 1a and keep the rest — the palette and type hold either way.
